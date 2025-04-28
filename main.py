import asyncio
import json
import logging
import pathlib
import random

from config import AppConfig, PersonalData, LoginInfo, SlotInfo
from datetime import date, datetime, timedelta, UTC
from utils import NoSlotsError
import nodriver as uc

script_dir = pathlib.Path(__file__).resolve().parent

class AppointmentCenterDetails:
    def __init__(
            self,
            center: str,
            category: str,
            sub_category: str,
    ):
        self.center = center
        self.category = category
        self.sub_category = sub_category

center_to_appointment_center_details = {
    'Ekaterinburg' : AppointmentCenterDetails('Ekaterinburg', 'Short Stay', 'Close relatives'),
    'Moscow' : AppointmentCenterDetails('Moscow', 'Short Stay', 'FAMILY VISIT'),
    'Vladivostok' : AppointmentCenterDetails('Vladivostok', 'Short Stay', 'FAMILY VISIT'),
    'Saint-Petersburg' : AppointmentCenterDetails('Saint-Petersburg', 'Short Stay', 'FAMILY VISIT'),
}

async def main(conf: AppConfig):
    while True:
        browser = await uc.start(browser_args=['--guest'])
        tab = await browser.get('https://visa.vfsglobal.com/rus/en/nld/login')
        try:
            await perform_login(tab, conf.login_info)

            await wait_loader(tab)
            await random_sleep(max_millis=1500)

            start_new_booking_button = await find_button_with_text(tab, 'Start New Booking')
            await start_new_booking_button.click()
            logging.info("Started new booking")

            await fill_appointment_details(tab, conf.centers)
            continue_button = await find_button_with_text(tab, text='Continue')
            await continue_button.click()

            await wait_loader(tab)
            await fill_personal_details(tab, conf.personal_data)

            await wait_loader(tab)
            continue_button = await find_button_with_text(tab, 'Continue')
            await continue_button.click()

            await select_slot(tab, conf.slot_info)
            await wait_loader(tab)
            continue_button = await find_button_with_text(tab, 'Continue')
            await continue_button.click()

            await wait_loader(tab)
            await review_appointment(tab)

            confirm_button = await find_button_with_text(tab, 'Confirm')
            await confirm_button.click()

            await wait_loader(tab)
            logging.info("Booked a slot")
            return
        except Exception as ex:
            if isinstance(ex, NoSlotsError):
                browser.stop()
                logging.info("No slots available, sleep for additional 1 minute")
                await asyncio.sleep(60)
            else:
                logging.exception("Caught an exception a slot booking:")
                # uncomment for debug
                # await asyncio.sleep(10000)
                await tab.save_screenshot(script_dir / f'{datetime.now(UTC).strftime("%Y-%m-%d_%H:%M:%S")}-result.jpeg', full_page=True)
                browser.stop()

        attempt_sleep = random.randint(20, 100)
        logging.info(f"Sleeping for {attempt_sleep} seconds before next attempt")
        await asyncio.sleep(attempt_sleep)

async def perform_login(tab: uc.Tab, login_info: LoginInfo):
    # cookie
    accept_cookies_button = await tab.select(selector='button[id="onetrust-accept-btn-handler"]')
    await accept_cookies_button.mouse_click()
    logging.info("Accepted cookies")
    # login
    email_input = await tab.select(selector='input[id="email"]')
    await email_input.send_keys(login_info.email)
    password_input = await tab.select(selector='input[id="password"]')
    await password_input.send_keys(login_info.password)
    logging.info("Filled email and password")

    try:
        signin_button = await find_button_with_text(tab, 'Sign In', timeout=5)
        await random_sleep(max_millis=500)
        await signin_button.mouse_click()
        logging.info("Clicked sign in button")
    except RuntimeError:
        logging.exception("Unable to press sign in button, most probably cf check")
        await tab.verify_cf()
        signin_button = await find_button_with_text(tab, 'Sign In')
        await random_sleep(max_millis=500)
        await signin_button.mouse_click()
        logging.info("Clicked sign in button")


async def fill_appointment_details(tab: uc.Tab, centers: list[str]):
    await tab.wait_for(selector='mat-card')
    logging.info("Awaited form with fields")

    for center in centers:
        await wait_loader(tab)
        await tab.scroll_up(amount=100)
        await random_sleep(max_millis=1000)

        centre_selector, category_selector, sub_category_selector = await tab.select_all(selector='mat-form-field')
        logging.info("Awaited dropdowns")

        appointment_center_details = center_to_appointment_center_details[center]

        await centre_selector.scroll_into_view()
        await centre_selector.mouse_click()
        center_dropdown_option = await find_dropdown_option_with_label(tab, appointment_center_details.center)
        await center_dropdown_option.click()
        logging.info("Selected center dropdown option")

        await wait_loader(tab)

        await category_selector.scroll_into_view()
        await category_selector.mouse_click()
        category_dropdown_option = await find_dropdown_option_with_label(tab, appointment_center_details.category)
        await category_dropdown_option.click()
        logging.info("Selected category dropdown option")

        await wait_loader(tab)
        await random_sleep(max_millis=1000)

        await sub_category_selector.scroll_into_view()
        await sub_category_selector.mouse_click()
        sub_category_dropdown_option = await find_dropdown_option_with_label(tab, appointment_center_details.sub_category)
        await sub_category_dropdown_option.click()
        logging.info("Selected sub-category dropdown option")

        await wait_loader(tab)

        alert_banner = await tab.select(selector='div.alert.alert-info.alert-info-blue')
        if alert_banner.text.find('no appointment slots') == -1:
            return

    raise NoSlotsError("There're no available slots")

async def fill_personal_details(tab: uc.Tab, personal_data: PersonalData):
    await wait_loader(tab)

    first_name_input = await find_input_with_label(tab, 'First Name')
    await first_name_input.send_keys(personal_data.first_name)

    last_name_input = await find_input_with_label(tab, 'Last Name')
    await last_name_input.send_keys(personal_data.last_name)

    gender_selector = await find_dropdown_with_label(tab, 'Gender')
    await gender_selector.scroll_into_view()
    await gender_selector.mouse_click()
    gender_selector_option = await find_dropdown_option_with_label(tab, personal_data.gender)
    await gender_selector_option.click()

    date_of_birth = await tab.select(selector='input[id="dateOfBirth"]')
    await date_of_birth.send_keys(personal_data.date_of_birth)

    nationality_selector = await find_dropdown_with_label(tab, 'Current Nationality')
    await nationality_selector.scroll_into_view()
    await nationality_selector.mouse_click()
    nationality_selector_option = await find_dropdown_option_with_label(tab, personal_data.nationality)
    await nationality_selector_option.click()

    passport_number_input = await find_input_with_label(tab, 'Passport Number')
    await passport_number_input.send_keys(personal_data.passport_number)

    passport_expiry_date_input = await tab.select(selector='input[id="passportExpirtyDate"]')
    await passport_expiry_date_input.send_keys(personal_data.passport_expiry_date)

    contact_number_county_code_input = await tab.select(selector='input[placeholder="44"]')
    await contact_number_county_code_input.send_keys(personal_data.contact_number_country_code)

    contact_number_rest_input = await tab.select(selector='input[placeholder="012345648382"]')
    await contact_number_rest_input.send_keys(personal_data.contact_number_rest)

    email_input = await find_input_with_label(tab, 'Email')
    await email_input.send_keys(personal_data.email)

    await tab.select(selector='div[id="mintime"]:empty', timeout=60)
    await random_sleep()

    save_button = await find_button_with_text(tab, 'Save')
    await save_button.click()

async def select_slot(tab: uc.Tab, slot_info: SlotInfo):
    today = date.today()
    from_date = today + timedelta(days=slot_info.now_start_interval_days)
    to_date = today + timedelta(days=slot_info.now_end_interval_days)

    while True:
        await wait_loader(tab)
        await tab.scroll_up(amount=300)
        # it takes some time to load slots
        await asyncio.sleep(2)

        logging.info("selecting all slots")
        all_month_slots = await tab.select_all(selector='td[data-date]')
        if len(all_month_slots) == 0:
            raise RuntimeError("No slots available")

        first_slot_date = parse_slot_date(all_month_slots[0].attrs['data-date'])
        if first_slot_date > to_date:
            raise RuntimeError("No available slots were found")

        last_slot_date = parse_slot_date(all_month_slots[-1].attrs['data-date'])
        if last_slot_date < from_date:
            logging.info("current last slot is too early, go to the next month")
            next_month_button = await find_next_month_calendar_button(tab)
            await next_month_button.click()
            continue

        for slot in all_month_slots:
            slot_date = parse_slot_date(slot.attrs['data-date'])
            if (slot_date >= from_date) and (slot_date <= to_date) and (slot.attrs['class_'].find('date-availiable') != -1):
                logging.info(f"day with slot was found for {slot_date} date, selecting it")
                await slot.scroll_into_view()
                await slot.children[0].mouse_click()
                await wait_loader(tab)
                logging.info("selecting slot time")
                select_slot_button = await tab.select(selector='input[type="radio"][name="SlotRadio"]')
                if select_slot_button is not None:
                    logging.info("found slot time button, clicking it")
                    await select_slot_button.scroll_into_view()
                    await select_slot_button.click()
                    return

        logging.info("slot wasn't found this month, go to the next month")
        next_month_button = await find_next_month_calendar_button(tab)
        await next_month_button.scroll_into_view()
        await next_month_button.click()

async def review_appointment(tab: uc.Tab):
    accept_terms_checkbox = await tab.select(selector='input[type="checkbox"][value="VAS T&Cs"]')
    await accept_terms_checkbox.click()

async def find_button_with_text(tab: uc.Tab, text: str, timeout: int = 10) -> uc.Element:
    buttons = await tab.select_all(selector='button:has(span[class="mdc-button__label"]):enabled', timeout=timeout)
    for button in buttons:
        if button.text.find(text) != -1:
            return button

    raise RuntimeError()

async def find_input_with_label(tab: uc.Tab, label: str) -> uc.Element:
    label_elems = await tab.select_all(selector='app-input-control > div > div')
    for label_elem in label_elems:
        if label_elem.text.find(label) != -1:
            return await label_elem.parent.query_selector(selector='input')

    raise RuntimeError(f'Unable to find an input with label {label}')

async def find_dropdown_with_label(tab: uc.Tab, label: str) -> uc.Element:
    dropdown_elems = await tab.select_all(selector='app-dropdown > div > div')
    for dropdown_elem in dropdown_elems:
        if dropdown_elem.text.find(label) != -1:
            return await dropdown_elem.parent.query_selector(selector='mat-form-field')

    raise RuntimeError(f'Unable to find a dropdown with label {label}')

async def find_dropdown_option_with_label(tab: uc.Tab, label: str) -> uc.Element:
    dropdown_options = await tab.select_all(selector='mat-option > span')
    for dropdown_option in dropdown_options:
        if dropdown_option.text.find(label) != -1:
            return await dropdown_option.parent

    raise RuntimeError(f'Unable to find a dropdown option with label {label}')

async def find_next_month_calendar_button(tab: uc.Tab) -> uc.Element:
    return await tab.select(selector='button[title="Next month"]')

async def wait_loader(tab: uc.Tab):
    logging.info("waiting loader")
    await tab.wait_for(selector='ngx-ui-loader > div[class="ngx-overlay"]', timeout=30)

def parse_slot_date(date_str: str) -> date:
    formate_date = '%Y-%m-%d'
    return datetime.strptime(date_str, formate_date).date()

def random_sleep(max_millis=5000):
    return asyncio.sleep(random.randint(500, max_millis) / 1000)

def parse_config(config_file_path: pathlib.Path) -> AppConfig:
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config_json = json.load(f)

        return AppConfig(
            login_info=LoginInfo(**config_json['login_info']),
            personal_data=PersonalData(**config_json['personal_data']),
            slot_info=SlotInfo(**config_json['slot_info']),
            centers=config_json['centers'],
        )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    config = parse_config(script_dir / 'config.json')
    uc.loop().run_until_complete(main(config))
