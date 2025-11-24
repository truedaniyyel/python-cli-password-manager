import sys
import secrets
import string
import json
import threading
import time
import getpass

try:
    import pyperclip
except ImportError:
    print("[!] Error: 'pyperclip' is missing. Run 'uv add pyperclip'")
    sys.exit(1)

try:
    from .security import SecurityManager
    from .storage import StorageManager
    from .views import VaultView
except ImportError as e:
    print(f"[!] Error: {e}")
    sys.exit(1)


class VaultController:
    def __init__(self):
        self.view = VaultView()
        try:
            self.db = StorageManager()
        except Exception as e:
            sys.exit(f"[!] DB Error: {e}")
        self.key = None

    # --- LOGIC HELPERS ---
    def _generate_password(self, length=24):
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))

    def _is_vault_empty(self):
        """
        Checks if DB has data. If empty, shows message and returns True.
        """
        if not self.db.get_all_blobs():
            self.view.show_message("[i] Vault is empty.")
            self.view.pause()
            return True
        return False

    def _clipboard_task(self, data):
        """Background task to clear clipboard."""
        time.sleep(60)
        if pyperclip.paste() == data:
            pyperclip.copy("")

    def _decrypt_all_entries(self):
        """Logic to get raw blobs and turn them into readable dicts."""
        raw_rows = self.db.get_all_blobs()
        decrypted = []
        for row_id, blob in raw_rows:
            try:
                json_bytes = SecurityManager.decrypt(blob, self.key)
                data = json.loads(json_bytes.decode('utf-8'))
                data['id'] = row_id
                decrypted.append(data)
            except Exception:
                continue
        return decrypted

    # --- FLOWS ---
    def login_flow(self):
        b64_salt = self.db.get_config("salt")

        if not b64_salt:
            # SETUP FLOW
            mp = self.view.setup_new_vault()
            generated_sk = secrets.token_hex(32)
            salt = SecurityManager.generate_salt()

            self.view.show_secret_key(generated_sk)

            self.key = SecurityManager.derive_key(mp, generated_sk, salt)
            validation_blob = SecurityManager.encrypt(b"VALID", self.key)

            self.db.save_config("salt", SecurityManager.encode_b64(salt))
            self.db.save_config("validation", SecurityManager.encode_b64(validation_blob))
            return

        # LOGIN FLOW
        salt = SecurityManager.decode_b64(b64_salt)
        validation_blob = SecurityManager.decode_b64(self.db.get_config("validation"))

        for attempts in range(3, 0, -1):
            mp, sk = self.view.get_master_credentials(attempts)
            try:
                derived_key = SecurityManager.derive_key(mp, sk, salt)
                check = SecurityManager.decrypt(validation_blob, derived_key)
                if check == b"VALID":
                    self.key = derived_key

                    del mp
                    del sk

                    self.view.show_message("[+] Access Granted.")
                    time.sleep(1)
                    return
            except Exception:
                del mp
                del sk

                if attempts > 1:
                    input("\n[-] Invalid credentials. Press Enter to retry...")

        sys.exit("\n[!] Security lockout.\n")

    def search_entries_flow(self):
        if self._is_vault_empty(): return

        while True:
            query = self.view.get_search_query()
            if not query:
                if 'all_entries' in locals(): del all_entries
                return

            all_entries = self._decrypt_all_entries()

            results = [
                e for e in all_entries
                if query in e['site'].lower() or query in e['username'].lower()
            ]

            if results:
                self.view.list_entries(results)
                self.view.pause()

                del all_entries
                del results
                return
            else:
                del all_entries
                del results

                if not self.view.ask_to_retry():
                    return

    def view_entries_flow(self):
        if self._is_vault_empty(): return

        entries = self._decrypt_all_entries()

        choice = self.view.get_sort_preference()
        match choice:
            case '2':
                entries.sort(key=lambda x: x['site'].lower())
            case '3':
                entries.sort(key=lambda x: x['username'].lower())
            case _:
                entries.sort(key=lambda x: x['id'])

        self.view.list_entries(entries)

        self.view.show_message("[Tip] Remember the ID if you want to Copy or Edit.")
        self.view.pause()

        del entries

    def copy_password_flow(self):
        if self._is_vault_empty(): return

        entries = self._decrypt_all_entries()
        self.view.list_entries(entries)

        while True:
            target_id = self.view.get_input("Enter ID to copy")
            if not target_id:
                del entries
                return

            target = next((e for e in entries if str(e['id']) == target_id), None)

            if target:
                pyperclip.copy(target['password'])
                self.view.show_message(f"[+] Password for {target['site']} copied!")
                threading.Thread(target=self._clipboard_task, args=(target['password'],), daemon=True).start()

                del target['password']
                del target
                del entries

                self.view.pause()
                return
            else:
                if not self.view.ask_to_retry():
                    del entries
                    return

    def add_entry_flow(self):
        result = self.view.get_entry_details()
        if not result: return

        site, username, pwd = result

        if pwd is None:
            pwd = self._generate_password()
            pyperclip.copy(pwd)
            self.view.show_message("[+] Password generated and copied to clipboard (clears in 60s).")
            threading.Thread(target=self._clipboard_task, args=(pwd,), daemon=True).start()

        data = {
            "site": site,
            "username": username,
            "password": pwd
        }
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted_blob = SecurityManager.encrypt(json_bytes, self.key)

        self.db.add_secret(encrypted_blob)

        del pwd
        del data
        del json_bytes

        self.view.show_message("[+] Saved.")
        self.view.pause()

    def edit_entry_flow(self):
        if self._is_vault_empty(): return

        entries = self._decrypt_all_entries()
        self.view.list_entries(entries)

        while True:
            target_id = self.view.get_input("Enter ID to edit")
            if not target_id:
                del entries
                return

            target = next((e for e in entries if str(e['id']) == target_id), None)

            if target:
                new_site, new_user, change_pwd = self.view.get_edit_values(target['site'], target['username'])

                new_pwd = target['password']
                if change_pwd:
                    if self.view.get_new_password_decision():
                        new_pwd = self._generate_password()
                        pyperclip.copy(new_pwd)
                        self.view.show_message("[+] New password generated and copied.")
                        threading.Thread(target=self._clipboard_task, args=(new_pwd,), daemon=True).start()
                    else:
                        new_pwd = getpass.getpass("New Password: ")

                save_data = {
                    "site": new_site,
                    "username": new_user,
                    "password": new_pwd
                }

                json_bytes = json.dumps(save_data).encode('utf-8')
                encrypted_blob = SecurityManager.encrypt(json_bytes, self.key)

                if self.db.update_secret(target_id, encrypted_blob):
                    self.view.show_message("[+] Entry updated successfully.")
                else:
                    self.view.show_message("[-] Database error.")

                del new_site, new_user

                if 'new_pwd' in locals(): del new_pwd

                del entries
                del target

                self.view.pause()
                return
            else:
                if not self.view.ask_to_retry():
                    del entries
                    return

    def delete_entry_flow(self):
        if self._is_vault_empty(): return

        entries = self._decrypt_all_entries()
        self.view.list_entries(entries)

        while True:
            target_id = self.view.get_input("Enter ID to delete")
            if not target_id:
                del entries
                return

            target = next((e for e in entries if str(e['id']) == target_id), None)

            if target:
                if self.view.confirm_delete(target['site']):
                    if self.db.delete_secret(target_id):
                        self.view.show_message("[+] Entry deleted.")
                    else:
                        self.view.show_message("[-] Error deleting from database.")
                else:
                    self.view.show_message("[i] Delete cancelled.")

                del target['password']
                del target
                del entries

                self.view.pause()
                return
            else:
                if not self.view.ask_to_retry():
                    del entries
                    return


    def run(self):
        try:
            self.login_flow()
            while True:
                choice = self.view.display_menu()

                match choice:
                    case '1':
                        self.search_entries_flow()
                    case '2':
                        self.view_entries_flow()
                    case '3':
                        self.copy_password_flow()
                    case '4':
                        self.add_entry_flow()
                    case '5':
                        self.edit_entry_flow()
                    case '6':
                        self.delete_entry_flow()
                    case 'q':
                        break
                    case _:
                        pass
        except KeyboardInterrupt:
            self.view.show_message("\n[!] Force Exit.")
        finally:
            self.db.close()
            print("\n[*] Database closed.")

            self.key = None
            del self.key

            print("[*] Exiting.")
            sys.exit()