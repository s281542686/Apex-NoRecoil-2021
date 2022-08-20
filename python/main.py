from modules.helpers import config_generator, read_config
from modules.recoil_patterns import recoil_patterns
from modules.native_controller import MouseMoveTo
from modules.banners import print_banner
from aip import AipOcr
from mss import mss
from mss import tools
import keyboard
import win32api
import time
import sys

sct = mss()
ocr_client = None

try:
    data = read_config()
    ocr_client = AipOcr(str(data["AppID"]), str(data["API_Key"]), str(data["Secret_Key"]))
except FileNotFoundError:
    try:
        config_generator()
        data = read_config()
        ocr_client = AipOcr(str(data["AppID"]), str(data["API_Key"]), str(data["Secret_Key"]))
    except KeyboardInterrupt:
        print_banner("single", "header-stop")
        print_banner("no-clear", "action-close-program")
        sys.exit(0)

toggle_button = "delete"


# 武器识别
def weapon_screenshot(select_weapon):
    if select_weapon == "one":
        image = sct.grab({
            "left": data["scan_coord_one"]["left"],
            "top": data["scan_coord_one"]["top"],
            "width": data["scan_coord_one"]["width"],
            "height": data["scan_coord_one"]["height"]
        })
        image = tools.to_png(image.rgb, image.size)
        return image
    elif select_weapon == "two":
        image = sct.grab({
            "left": data["scan_coord_two"]["left"],
            "top": data["scan_coord_two"]["top"],
            "width": data["scan_coord_two"]["width"],
            "height": data["scan_coord_two"]["height"]
        })
        image = tools.to_png(image.rgb, image.size)
        return image
    else:
        print("ERROR: Invalid weapon selection | FUNC: weapon_screenshot")
        print(f"VALUE: select_weapon = {select_weapon}")
        sys.exit(1)


def read_weapon(png_image):
    # 调用通用文字识别（标准含位置信息版）
    res_image = ocr_client.general(png_image)
    if res_image.get("words_result") is None:
        # 调用通用文字识别（高精度版）
        res_image = ocr_client.basicAccurate(png_image)
    elif res_image.get("words_result") is None:
        # 调用通用文字识别（高精度含位置版）
        res_image = ocr_client.accurate(png_image)
    elif res_image.get("words_result") is None:
        # 网络文字识别
        res_image = ocr_client.webImage(png_image)
    elif res_image.get("words_result") is None:
        # 通用文字识别
        res_image = ocr_client.basicGeneral(png_image)
    if res_image.get("words_result") is not None:
        return res_image.get("words_result")[0].get("words")
    return "None"

def left_click_state():
    left_click = win32api.GetKeyState(0x01)
    return left_click < 0


def right_click_state():
    right_click = win32api.GetKeyState(0x02)
    return right_click < 0


active_state = False
last_exit_status = False
active_weapon = "None"
supported_weapon = False

print_banner("double", "header-start", "user-options")

# LISTENER: Keyboard & Mouse Input
try:
    while True:
        exit_status = keyboard.is_pressed(toggle_button)

        print(
            f"RECOIL-CONTROL: {active_state} | ACTIVE-WEAPON: {active_weapon} | SUPPORTED: {supported_weapon}",
            end=" \r")

        # TOGGLE: Enable/Disable Recoil-Control
        if exit_status != last_exit_status:
            last_exit_status = exit_status
            if last_exit_status:
                active_state = not active_state

        if active_state is False:
            supported_weapon = active_state

        # OPTION: Read Weapon-Slot & Apply Recoil-Pattern
        if active_state and keyboard.is_pressed("1"):
            try:
                active_weapon = read_weapon(weapon_screenshot("one"))
                supported_weapon = recoil_patterns.get(active_weapon) is not None
            except Exception:
                supported_weapon = False
                continue

        # OPTION: Read Weapon-Slot & Apply Recoil-Pattern
        if active_state and keyboard.is_pressed("2"):
            try:
                active_weapon = read_weapon(weapon_screenshot("two"))
                supported_weapon = recoil_patterns.get(active_weapon) is not None
            except Exception:
                supported_weapon = False
                continue

        # ACTION: Apply Recoil-Control w/ Left-Click
        if supported_weapon and right_click_state():
            try:
                for i in range(len(recoil_patterns[active_weapon])):
                    if left_click_state():
                        MouseMoveTo(int(recoil_patterns[active_weapon][i][0] / data["modifier_value"]),
                                    int(recoil_patterns[active_weapon][i][1] / data["modifier_value"]))
                        time.sleep(recoil_patterns[active_weapon][i][2])
            except Exception:
                continue

        # OPTION: Kill Program
        if keyboard.is_pressed("F12"):
            print_banner("single", "header-stop")
            print_banner("no-clear", "action-close-program")
            sys.exit(0)

        # DELAY: While-Loop | Otherwise stuttering issues in-game
        time.sleep(0.002)
except KeyboardInterrupt:
    print_banner("single", "header-stop")
    print_banner("no-clear", "action-close-program")
    sys.exit(0)
