import datetime

class LoginInfo:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

class PersonalData:
    def __init__(
            self,
            first_name: str,
            last_name: str,
            gender: str,
            date_of_birth: str,
            nationality: str,
            passport_number: str,
            passport_expiry_date: str,
            contact_number_country_code: str,
            contact_number_rest: str,
            email: str,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.nationality = nationality
        self.passport_number = passport_number
        self.passport_expiry_date = passport_expiry_date
        self.contact_number_country_code = contact_number_country_code
        self.contact_number_rest = contact_number_rest
        self.email = email

class SlotInfo:
    def __init__(
            self,
            now_start_interval_days: int,
            now_end_interval_days: int,
    ):
        if now_end_interval_days < now_start_interval_days:
            raise ValueError("now_end_interval_days can't be less than now_start_interval_days")

        self.now_start_interval_days = now_start_interval_days
        self.now_end_interval_days = now_end_interval_days

class AppConfig:
    def __init__(
            self,
            login_info: LoginInfo,
            personal_data: PersonalData,
            slot_info: SlotInfo,
            centers: list[str],
    ):
        self.login_info = login_info
        self.personal_data = personal_data
        self.slot_info = slot_info
        self.centers = centers
