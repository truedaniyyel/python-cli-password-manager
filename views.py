import os
import getpass

class VaultView:
    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def pause():
        input("\nPress Enter...")

    def get_input(self, prompt=""):
        return input(f"\n{prompt} (Press Enter to Back): ").strip()

    def show_message(self, msg):
        print(f"\n{msg}")

    def ask_to_retry(self):
        """Returns True if user wants to retry, False otherwise."""
        return input("\n[-] No matches. Try again? (y/n): ").strip().lower() == 'y'


    def get_sort_preference(self):
        """
        Displays sorting options and returns the user's choice string.
        """
        print("\nSort by: [1] ID (Default)  [2] Website  [3] Username")
        return input("Choice (Press Enter for Default): ").strip()


    def display_menu(self):
        self.clear_screen()

        print("1. Search")
        print("2. View All (Masked)")
        print("3. Copy Password")
        print("4. Add Password")
        print("5. Edit Entry")
        print("6. Delete")
        print("q. Quit")
        return input("\nChoice: ").strip()


    def setup_new_vault(self):
        self.clear_screen()

        print("╔════════════════════════════════════════╗")
        print("║      NEW VAULT SETUP INITIALIZED       ║")
        print("╚════════════════════════════════════════╝")

        while True:
            mp = getpass.getpass("1. Choose Master Password (min 8 chars): ")
            if len(mp) < 8:
                print("\n   [!] Too weak.\n")
                continue
            confirm = getpass.getpass("   Confirm Master Password: ")
            if confirm != mp:
                print("\n   [!] Mismatch.\n")
                continue
            return mp


    def show_secret_key(self, key):
        print(f"\n[!] SECRET KEY: {key}")
        print("\n⚠  SAVE THIS KEY. IT WILL NOT BE SHOWN AGAIN. ⚠")
        input("\nPress Enter after saving...")


    def get_master_credentials(self, attempts_left):
        self.clear_screen()

        print(f"--- LOCKED VAULT (Attempts: {attempts_left}) ---")

        mp = getpass.getpass("Master Password: ")
        sk = getpass.getpass("Secret Key: ").strip()
        return mp, sk


    def list_entries(self, entries):
        """Expects a list of dicts: {'id', 'site', 'username'}"""
        self.clear_screen()

        print(f"{'ID':<5} {'WEBSITE':<25} {'USERNAME':<25} {'PASSWORD'}")
        print("-" * 80)
        for entry in entries:
            masked_pwd = "*" * 8
            print(f"{entry['id']:<5} {entry['site']:<25} {entry['username']:<25} {masked_pwd}")


    def get_search_query(self):
        self.clear_screen()

        print("--- SECURE SEARCH ---")
        return self.get_input("Search term (Site/User)").lower()


    def get_entry_details(self):
        self.clear_screen()

        print("--- NEW ENTRY ---")

        site = self.get_input("Website")
        if not site: return None
        username = input("Username: ")

        if input("Generate password? (y/n): ").lower() == 'y':
            return site, username, None

        pwd = getpass.getpass("Password: ")
        return site, username, pwd


    def get_edit_values(self, current_site, current_user):
        """
        Shows current values and allows user to press Enter to keep them.
        Returns: (new_site, new_username, change_password_bool)
        """
        self.clear_screen()

        print(f"--- EDITING: {current_site} ---")
        print("(Press Enter to keep current value)")

        new_site = input(f"\nWebsite [{current_site}]: ").strip() or current_site
        new_user = input(f"Username [{current_user}]: ").strip() or current_user

        change_pwd = input("Change password? (y/n): ").lower() == 'y'

        return new_site, new_user, change_pwd


    def get_new_password_decision(self):
        """Returns True for 'generate', False for 'manual input'"""
        return input("Generate new password? (y/n): ").lower() == 'y'


    def confirm_delete(self, site_name):
        """
        Asks for explicit confirmation.
        Returns True if user types 'y', False otherwise.
        """
        print(f"\n[!!!] WARNING: You are about to delete the entry for '{site_name}'.")
        ans = input("Are you sure? This cannot be undone. (y/n): ").lower()
        return ans == 'y'