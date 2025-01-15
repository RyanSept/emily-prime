"""
1. read ./data/contacts-export.csv and transform
2. For each row,
    3. Make _name_ as concatenation of First Name,Middle Name,Last Name
    4. For each of phone numbers
        5. Take the phone number and normalize it
        6. Add to global dictionary with key as phone number and value as _name_.
            if number exists, leave value as it is but log out
7. Write to ./data/contacts-export.json
"""
import csv
import os
import json

import phonenumbers

from constants import CONTACTS_CSV_PATH, CONTACTS_JSON_PATH, ROOT_DIR

with open(CONTACTS_JSON_PATH, 'r') as f:
    CONTACTS_JSON = json.load(f)

def normalize_number(number: str):
    # remove + such that +1234567890 becomes 1234567890
    format_whatsapp = lambda n: phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)[1:]

    try:
        parsed_n: phonenumbers.PhoneNumber = phonenumbers.parse(number, "KE")
        return format_whatsapp(parsed_n)
    except phonenumbers.phonenumberutil.NumberParseException:
        print(f"Could not parse number {number}")
        try:
            parsed_n: phonenumbers.PhoneNumber = phonenumbers.parse(number, "PT")
            return format_whatsapp(parsed_n)
        except phonenumbers.phonenumberutil.NumberParseException:
            print(f"Could not parse number {number}")
            raise SystemError(f"Could not parse number {number}")

def process_contacts():
    contacts = {}
    with open(CONTACTS_CSV_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            numbers = []
            for number in [ row["Phone 1 - Value"], row["Phone 2 - Value"], row["Phone 3 - Value"], row["Phone 4 - Value"] ]:
                # remove empty strings
                if not number:
                    continue
                elif ":::" in number:
                    numbers += number.split(":::")
                else:
                    numbers += [number]

            name = f"{row['First Name']} {row['Middle Name']} {row['Last Name']}".strip()
            name = "Unknown" if name == "" else name
            for number in numbers:
                normalized_number = normalize_number(number)
                if normalized_number in contacts:
                    print(f"Number {normalized_number} already exists with name {contacts[normalized_number]}")
                    continue
                contacts[normalized_number] = name
    return contacts

def write_contacts(contacts):
    with open(CONTACTS_JSON_PATH, 'w') as f:
        json.dump(contacts, f, indent=4)

def get_contact_name(number: str) -> str:
    return CONTACTS_JSON.get(number, f"Unknown-{number}")

def main():
    contacts = process_contacts()
    write_contacts(contacts)

if __name__ == "__main__":
    main()
