import requests
import json
import pandas as pd
from tabulate import tabulate
import pickle
import datetime


class StackOverflowUsers:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.stackexchange.com/2.2"
        self.bookmarked_users = set()
        self.fetched_users = {}
        self.load_bookmarked_users()

    def load_bookmarked_users(self):
        try:
            with open("bookmarked_users.pkl", "rb") as file:
                self.bookmarked_users = pickle.load(file)
        except FileNotFoundError:
            pass

    def save_bookmarked_users(self):
        with open("bookmarked_users.pkl", "wb") as file:
            pickle.dump(self.bookmarked_users, file)

    def fetch_users(self, page=1, pagesize=100, sort_order="desc"):
        pagesize = min(pagesize, 100)
        try:
            response = requests.get(
                f"{self.base_url}/users",
                params={
                    "key": self.api_key,
                    "order": sort_order,
                    "site": "stackoverflow",
                    "page": page,
                    "pagesize": pagesize
                },
            )
            response.raise_for_status()
            data = response.json()
            users = data["items"]


            for user in users:
                user_id = user.get("user_id")
                if user_id:
                    self.fetched_users[user_id] = user

            return users
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e.response.content}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users: {str(e)}")
            return []

    def display_users(self, users):
        if not users:
            print("No users to display.")
            return

        user_data = []
        counter = 1
        for user in users:
            last_access_date = datetime.datetime.fromtimestamp(
                user.get("last_access_date", 0)
            ).strftime('%Y-%m-%d %H:%M:%S')

            user_data.append(
                {
                    "User Number": counter,
                    "Name": user.get("display_name", "Null"),
                    "UserID": user.get("user_id", "Null"),
                    "Reputation": user.get("reputation", "Null"),
                    "LastAccessDate": last_access_date,
                }
            )
            counter += 1

        df = pd.DataFrame(user_data)
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

    def save_users_to_file(self, file_name, sort_order="asc", users=None):
        if users is None:
            print("Fetching users...")
            users = self.fetch_users()

        if not users:
            print("No users to save. Fetch and display users first.")
            return

        if sort_order == "asc":
            users.sort(key=lambda user: user.get("user_id", 0))
        elif sort_order == "desc":
            users.sort(key=lambda user: user.get("user_id", 0), reverse=True)

        user_data = []
        for user in users:
            last_access_date = datetime.datetime.fromtimestamp(
                user.get("last_access_date", 0)
            ).strftime('%Y-%m-%d %H:%M:%S')
            user_data.append([
                user.get("user_id", "Null"),
                user.get("account_id", "Null"),
                user.get("display_name", "Null").replace("\t", " "),
                user.get("age", "Null"),
                user.get("reputation", "Null"),
                user.get("location", "Null").replace("\t", " ") if user.get("location") else "Null",
                user.get("user_type", "Null"),
                last_access_date
            ])

        headers = ["UserID", "AccountID", "DisplayName", "UserAge", "Reputation", "Location", "UserType", "LastAccessDate"]
        table = tabulate(user_data, headers, tablefmt="grid")

        if not file_name.endswith(".sofusers"):
            file_name += ".sofusers"

        try:
            with open(file_name, "w", encoding='utf-8') as file:
                file.write(f"Total Count of Users Fetched: {len(users)}\n")
                file.write(f"Total Count of Pages: {1}\n")
                file.write(table)
            print(f"Users have been successfully saved to {file_name}")
        except Exception as e:
            print(f"Error saving users to file: {str(e)}")

    def bookmark_user(self, user_id):

        user_id = int(user_id) if user_id.isdigit() else user_id

        if user_id in self.fetched_users:
            self.bookmarked_users.add(user_id)
            self.save_bookmarked_users()
            print(f"User with ID {user_id} has been bookmarked.")
        else:
            print(f"User ID {user_id} not found in fetched users. Please fetch users before bookmarking.")

    def unbookmark_user(self, user_id):
        user_id = int(user_id) if user_id.isdigit() else user_id

        if user_id in self.bookmarked_users:
            self.bookmarked_users.remove(user_id)
            self.save_bookmarked_users()
            print(f"User with ID {user_id} has been unbookmarked.")
        else:
            print(f"User with ID {user_id} is not bookmarked. Please check the bookmarked user list.")

    def display_bookmarked_users(self):
        if not self.bookmarked_users:
            print("No users are bookmarked.")
            return


        bookmarked_users = []
        for user_id in self.bookmarked_users:
            user_info = self.fetch_user_info(user_id)
            if user_info:
                bookmarked_users.append(user_info)

        if bookmarked_users:
            print("Bookmarked Users:")
            self.display_users(bookmarked_users)
        else:
            print("No bookmarked users found.")

    def fetch_user_info(self, user_id):
        try:
            response = requests.get(
                f"{self.base_url}/users/{user_id}",
                params={
                    "key": self.api_key,
                    "site": "stackoverflow"
                },
            )
            response.raise_for_status()
            data = response.json()
            user_info = data["items"][0]
            return user_info
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e.response.content}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user information: {str(e)}")
            return None


if __name__ == "__main__":
    api_key = "xrsZng3Cq90hSs4H5FMngQ(("
    manager = StackOverflowUsers(api_key)

    while True:
        print("\nMenu:")
        print("1. Fetch and display Stack Overflow users")
        print("2. Save users to file (Specify sort order: asc or desc)")
        print("3. Bookmark a user")
        print("4. Unbookmark a user")
        print("5. Display bookmarked users")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            pageNum = input("Enter the page number: ")
            try:
                pageNum_int = int(pageNum)
                if pageNum_int > 0:
                    pagesize = input("Enter the number of users per page (Max number of users per page = 100): ")
                    try:
                        pagesize_int = int(pagesize)
                        if pagesize_int > 0 and pagesize_int <= 100:
                            users = manager.fetch_users(page=int(pageNum), pagesize=pagesize_int)
                            manager.display_users(users)
                        else:
                            print("Number of user per page must between 1 and 100.")
                    except ValueError:
                        print(f"Invalid Number of user: {pagesize}. Number of user must be a valid integer.")
                else:
                    print(f"Invalid page number: {pageNum}. Page number must be a positive integer greater than 0.")
            except ValueError:
                print(f"Invalid page number: {pageNum}. Page number must be a valid integer.")

        elif choice == "2":
            while True:
                file_name = input("Enter the file name to save users: ").strip()
                if file_name:
                    break
                else:
                    print("File name cannot be empty. Please enter a valid file name.")
            sort_order = input("Enter sort order (asc or desc): ").lower().strip()
            while sort_order not in ['asc', 'desc']:
                print("Invalid sort order. Please enter 'asc' for ascending or 'desc' for descending.")
                sort_order = input("Enter sort order (asc or desc): ").lower().strip()
            try:
                users_to_save = manager.fetch_users()
                manager.save_users_to_file(file_name, sort_order, users_to_save)

            except Exception as e:
                print(f"An error occurred: {e}")
        elif choice == "3":
            user_id = input("Enter the user ID to bookmark: ")
            manager.bookmark_user(user_id)
        elif choice == "4":
            user_id = input("Enter the user ID to unbookmark: ")
            manager.unbookmark_user(user_id)
        elif choice == "5":
            manager.display_bookmarked_users()
        elif choice == "6":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter a valid option.")
