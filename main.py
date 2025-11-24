from controller import VaultController

def main():
    try:
        app = VaultController()
        app.run()
    except KeyboardInterrupt:
        print("\n[!] Exiting.")
    except Exception as e:
        print(f"\n[!] Fatal Error: {e}")

if __name__ == "__main__":
    main()