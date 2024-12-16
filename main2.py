import cv2, keyboard, threading, requests, pyautogui, datetime, sys
import  pydirectinput, time
import keys
from windowcapture import WindowCapture
from fisch import FischVision
from PIL import ImageGrab

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from interface import ProgramInterfaceGUI


last_left_release_time = 0

wincap = WindowCapture('Roblox')

fisch = FischVision()
xBarPosition = None

shake_img = 'shake.png'


config = {
            "DISCORD_WEBHOOK": "",
            "quadrado_bar": [238, 495, 380, 30],
            "barra_quadrado_bar": [238, 503, 324, 13],
            "quadrado_bar_progresso": [310, 531, 178, 4],
            "shake_area": [150, 50, 550, 450],
            "catch_delay": 2,
            "max_repeating_duration": 30,
            "tolerance": 5,
            "max_hold_time": 2.0,
            "min_hold_time": 0.1,
            "target_fish_x": 450,
            "target_hold_time": 3,
            "left_bound_x": 350
}

last_space_release_time = 0
previous_fish_x = None
previous_bar_x = None
previous_distance = None

DISCORD_WEBHOOK = config['DISCORD_WEBHOOK']




def holdSpace(holdTime):
    #keys.PressKey(0x39)
    threading.Timer(holdTime, keys.PressKey, args=(0x39,)).start()
    

def calculate_velocity(current_pos, previous_pos, time_interval):

    return (current_pos - previous_pos) / time_interval


def autoFishMicroAjust2(bar, fish, tolerance=5, max_hold_time=2.0, min_hold_time=0.1, target_fish_x=450, target_hold_time=3, left_bound_x=350):
    global last_left_release_time

    # extracts the center coordinates of bar and fish
    bar_x, bar_y, bar_w, bar_h = bar
    fish_x, fish_y, fish_w, fish_h = fish
    
    fish_center_x = fish_x + fish_w // 2
    bar_center_x = bar_x + bar_w // 2

    area_de_confronto = (238, 503, 324, 13)
    area_x, area_y, area_w, area_h = area_de_confronto

    distance_to_center = 0  

    num_squares = 5
    square_width = area_w // num_squares
    square_positions = [(area_x + i * square_width, area_x + (i + 1) * square_width) for i in range(num_squares)]
    
    #when lower the value, the faster the bar drops to that location
    left_move_delays = [0.1, 0.2, 0.5, 0.05, 0.05] 

    fish_square, bar_square = None, None
    for i, (square_start, square_end) in enumerate(square_positions):
        if square_start <= fish_center_x <= square_end:
            fish_square = i
        if square_start <= bar_center_x <= square_end:
            bar_square = i

    if fish_x <= left_bound_x:
        print("Peixe no limite esquerdo - sem movimento da barra")
        keys.ReleaseKey(0x39)
        hold_time = 0
        left_move_delay_pclick = 0

    elif fish_x >= target_fish_x:
        print("Peixe no limite direito - sem delay e hold_time máximo")
        hold_time = target_hold_time
        left_move_delay_pclick = 0
        holdSpace(hold_time)  

    else:
        distance_to_center = abs(fish_center_x - bar_center_x)
        distance_to_center = distance_to_center - 3

        hold_time = min_hold_time + (distance_to_center / bar_w) * (max_hold_time - min_hold_time)
        hold_time = min(hold_time, max_hold_time)

        left_move_delay_pclick = min(0.5, 0.01 + distance_to_center / 100)
        print(f"delay left: {left_move_delay_pclick}")

        # Lógica de controle de movimento
        if fish_center_x > bar_center_x + tolerance:
            print(f"Movendo para a direita com holdTime = {hold_time:.2f}")
            holdSpace(hold_time)
            
        elif fish_center_x < bar_center_x - tolerance:

            current_time = time.time()
            specific_delay = left_move_delays[fish_square] 

            if current_time - last_left_release_time >= specific_delay:
                print(f"Movendo para a esquerda - liberando `space` para retornar (delay específico = {specific_delay}s)")
                keyboard.release('space')
                last_left_release_time = current_time

            #current_time = time.time()
            #if current_time - last_left_release_time >= left_move_delay_pclick:
            #    print("Movendo para a esquerda - soltando o space")
            #    last_left_release_time = current_time
            
        else:
            print("Peixe centralizado - mantendo posição")
            keyboard.release('space')
    
    display_info = {
        "Bar Position": {"x": bar_x, "y": bar_y, "width": bar_w, "height": bar_h},
        "Fish Position": {"x": fish_x, "y": fish_y, "width": fish_w, "height": fish_h},
        "Tolerance Area": {
            "left_bound": bar_center_x - tolerance,
            "right_bound": bar_center_x + tolerance,
            "center_x": bar_center_x
        },
        "Distance to Center": distance_to_center,
        "Hold Time": hold_time,
        "Left Move Delay": left_move_delay_pclick
    }

    return display_info



def autoFishMicroAjust(bar, fish, tolerance=3, target_fish_x=450, left_bound_x=350, fps=40):
    global last_space_release_time, previous_fish_x, previous_bar_x, previous_distance_to_center

    bar_x, bar_y, bar_width, bar_height = bar
    fish_x, fish_y, fish_width, fish_height = fish

    fish_center_x = fish_x + fish_width // 2
    bar_center_x = bar_x + bar_width // 2
    distance_between_fish_and_bar = fish_center_x - bar_center_x

    #visual = represent_bar_and_fish(bar_x, bar_width, fish_x, fish_width)
   # print(f"Visualização: {visual}")

    time_interval = 1 / fps

    if previous_fish_x is None:
        previous_fish_x = fish_center_x
        previous_bar_x = bar_center_x
        previous_distance_to_center = distance_between_fish_and_bar

    fish_movement_speed = calculate_velocity(fish_center_x, previous_fish_x, time_interval)
    bar_movement_speed = calculate_velocity(bar_center_x, previous_bar_x, time_interval)
    distance_change_rate = calculate_velocity(distance_between_fish_and_bar, previous_distance_to_center, time_interval)

    previous_fish_x = fish_center_x
    previous_bar_x = bar_center_x
    previous_distance_to_center = distance_between_fish_and_bar

    force_factor_a = 0.3
    speed_factor_b = 0.03
    bar_velocity_factor_c = 0.02
    distance_scaling_g = 0.5
    adjusted_initial_velocity = bar_movement_speed - (force_factor_a / fps)

    # hold_time calculation
    calculation_term1 = max(
        force_factor_a * (adjusted_initial_velocity**2 * distance_scaling_g +
                          (force_factor_a - distance_scaling_g) * distance_between_fish_and_bar * distance_scaling_g +
                          (fish_movement_speed**2)), 0)
    hold_time_1 = -((calculation_term1**0.5 + adjusted_initial_velocity * force_factor_a) / -490 * 2)

    hold_time_2 = (force_factor_a * distance_between_fish_and_bar) + \
                  (speed_factor_b * distance_change_rate) + \
                  (bar_velocity_factor_c * bar_movement_speed)
    hold_time_2 = (hold_time_2**0.5 if hold_time_2 > 0 else -(-hold_time_2)**0.5)

    hold_time = round(hold_time_1 * 1 + hold_time_2 * 0.1, 4)

    hold_cooldown = max(0.1, 0.05 + abs(distance_between_fish_and_bar) / 300)

    current_time = time.time()

    #if fish_x >= target_fish_x:
    #    print("Peixe no limite direito - forçando `hold_time` máximo")
    #    keyboard.release('space')
    #    hold_time = 0.6  # Segurar para mover continuamente
    #    hold_cooldown = 0  # Sem atraso
    #    last_space_release_time = current_time
    #    holdSpace(hold_time)
    #    return
    #elif fish_x <= left_bound_x:
    #    print("Peixe no limite esquerdo - sem movimento da barra")
    #    return

    if fish_center_x > bar_center_x + tolerance:

        # quando o peixe está fora da barra
        if fish_x + fish_width < bar_x or fish_x > bar_x + bar_width:
            hold_cooldown = max(0.5, 0.05 + abs(distance_between_fish_and_bar) / 300)
            if current_time - last_space_release_time >= hold_cooldown:
                hold_time = round(hold_time_1 * 1.5 + hold_time_2 * 0.1, 4)
                print(f"[PEIXE FORA DA BARRA] [Direita] last_space_release_time: {last_space_release_time:.4f} | current_time: {current_time:.4f} | hold_cooldown: {hold_cooldown:.4f} | hold_time: {hold_time:.4f} | X da bar atual: {bar_x} | distância da barra para o peixe: {distance_between_fish_and_bar} | X do fish: {fish_x}")
                holdSpace(hold_time)
                last_space_release_time = current_time

        elif current_time - last_space_release_time >= hold_cooldown:
            print(f"[Direita] last_space_release_time: {last_space_release_time:.4f} | current_time: {current_time:.4f} | hold_cooldown: {hold_cooldown:.4f} | hold_time: {hold_time:.4f} | X da bar atual: {bar_x} | distância da barra para o peixe: {distance_between_fish_and_bar} | X do fish: {fish_x}")
            holdSpace(hold_time)
            last_space_release_time = current_time


    elif fish_center_x < bar_center_x - tolerance:
        left_release_delay = abs(distance_between_fish_and_bar) / 300
        if current_time - last_space_release_time >= left_release_delay:
            print(f"[Esquerda] Movendo para a esquerda - liberando `space` | delay: {left_release_delay:.4f} | current_time: {current_time:.4f} | last_space_release_time: {last_space_release_time:.4f} | distância da barra para o peixe: {distance_between_fish_and_bar} | X do fish: {fish_x} | X da bar atual: {bar_x}")
            keyboard.release('space')
            last_space_release_time = current_time

    else:
        print(f"[Centralizado] Peixe centralizado - mantendo posição | X da bar atual: {bar_x} | distância da barra para o peixe: {distance_between_fish_and_bar} | X do fish: {fish_x}")
        keyboard.release('space')

def perform_catch():
    pydirectinput.mouseDown()
    time.sleep(1.5) 
    pydirectinput.mouseUp()

space_pressed_until = None



def sendDiscordNotification(content, color):
    data = {
        "content": None,
        "embeds": [
          {
            "title": "Fisch",
            "description": content,
            "color": color
          }
        ],
        "username": "Fisch",
        "attachments": []
    }

    r =  requests.post(DISCORD_WEBHOOK, json=data)
    if r.status_code == 204:
        print("Discord notification sent!")
    else:
        print("Discord notification error!", r.status_code , r.text)


def sync_config(new_config):
    """Callback to update the global config."""
    print("snc config")
    global config
    config.update(new_config)


def main():
    global xBarPosition



    app = QApplication(sys.argv)
    gui = ProgramInterfaceGUI(update_callback=sync_config)
    gui.show()

    
    gui.add_log_entry("Init")

    rightClickFixPerfom = wincap.get_screen_position((400, 300))


    is_catching = False
    is_key_sequence_active = False
    is_repeating_keys = False
    catch_start_time = None
    repeating_keys_start_time = None
    fishCatch = 0
    fishLost = 0

    started = False
    cv2.namedWindow("Detected")
    cv2.namedWindow("ROI")
    cv2.namedWindow("Gray")
    cv2.namedWindow("Edges")
    cv2.namedWindow("Contours")
    fisch.create_trackbars()
    loop_time = time.time()




    while True:
        config = gui.config
        # x, y ,w , h
        quadrado_bar = (config['quadrado_bar'][0], config['quadrado_bar'][1], config['quadrado_bar'][2], config['quadrado_bar'][3])
        barra_quadrado_bar = (config['barra_quadrado_bar'][0], 503, 324, 13)
        quadrado_bar_progresso = (310, 531, 178,  4)
        shake_area = (config['shake_area'][0], 50, 550,  450)
        catch_delay = config['catch_delay']
        max_repeating_duration = config['max_repeating_duration']
        start_time = time.time()  

        screenshot = wincap.get_screenshot()
        if screenshot is not None:

            rgb_frame = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)

            gui.update_roi(rgb_frame)

        offsets = wincap.offset_x, wincap.offset_y
        screen = screenshot
        wincap.resize_window(width=800,height=600)
        current_fps = 1 / (time.time() - loop_time)
        loop_time = time.time()

        if screen is None:
            break

        if keyboard.is_pressed('q'):
            print("Saindo... (Q apertado)")
            break

        if keyboard.is_pressed('l') and not started:
            print("Iniciado (L apertado)")
            wincap.setForegroundWindow()
            started = True

        fishBar, roi, gray, edges, contours = fisch.getFishBar(screen, barra_quadrado_bar)
        fishColumn = fisch.getFishColumn(screen, quadrado_bar)
        progressBar, roi, gray, edges, contours  = fisch.getProgressBar(screen, quadrado_bar_progresso)
#
        if roi is not None:
            cv2.imshow("ROI", roi)
            rgb_frame2 = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
           # gui.update_roi2(rgb_frame2)
        if gray is not None:
            cv2.imshow("Gray", gray)
        if edges is not None:
            cv2.imshow("Edges", edges)
            contours_img = roi.copy()
            cv2.drawContours(contours_img, contours, -1, (0, 255, 0), 2)
            cv2.imshow("Contours", contours_img)
#
        #wincap.setForegroundWindow()
        if started:
            
            
            if not is_catching and not fishColumn and not fishBar:
                if catch_start_time is None:
                    catch_start_time = time.time()
                elif time.time() - catch_start_time >= catch_delay:
                    # Case 1
                    print("Perform catch foi executado")
                    wincap.setForegroundWindow()
                    perform_catch()
                    is_catching = True
                    catch_start_time = None
                    notification_sent = False
                    keyboard.press_and_release(']')
#
            elif is_catching and not is_key_sequence_active and not fishColumn:
                # Case 2: Press ] only once
                print("Pressionando `]` uma vez para iniciar o modo de captura")
                is_key_sequence_active = True
                is_repeating_keys = True
                repeating_keys_start_time = time.time()  
            if wincap.isWindowOpen() and is_repeating_keys and not fishColumn:
                shakeCirclePos = fisch.getShake(screen, offsets, roi=shake_area)
                # Case 2 continues: Repeat s and enter until fishColumn is True
                
                if repeating_keys_start_time and (time.time() - repeating_keys_start_time >= max_repeating_duration):
                    print("Reiniciando captura após 30 segundos sem fishColumn")
                    is_repeating_keys = False
                    is_catching = False
                    is_key_sequence_active = False
                    repeating_keys_start_time = None
                    continue
                
                click = False
                if shakeCirclePos and click:
                    #pos = wincap.get_screen_position((shakeCirclePos[0], shakeCirclePos[1]))
                    print("identificou")
                    pyautogui.moveTo(shakeCirclePos[0], shakeCirclePos[1])
                    time.sleep(0.1)
                    print("delay")
                    pydirectinput.click(shakeCirclePos[0], shakeCirclePos[1])
                else:
                    keyboard.press_and_release('s')
                    keyboard.press_and_release('enter')



            elif fishColumn:
                
                # Case 3: Fish detected - reset capture mode and stop key sequence
                is_catching = False
                is_key_sequence_active = False
                is_repeating_keys = False
                repeating_keys_start_time = None
   
                fish = fishColumn[0]
                x, y, w, h = fish
                cv2.rectangle(screen, (x, y), (x + w, y + h), (182, 123, 255), 2)
                cv2.putText(screen, f"Peixe - Pos: ({x}, {y}) W: {w} H: {h}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (182, 123, 255), 1)
#
                if fishBar and wincap.isWindowOpen():
                    bar = fishBar[0]
#
                    bar_x, bar_y, bar_w, bar_h = bar
                    display_info = autoFishMicroAjust2(bar=bar, fish=fish, tolerance=config['tolerance'], max_hold_time=config['max_hold_time'], min_hold_time=config['min_hold_time'])
#
                    divisao = 5
                                         # x    y    w   h 
                    barra_quadrado_bar = (238, 503, 324, 13)
                    
                    square_width = barra_quadrado_bar[2] // divisao  
                    
                    # this is responsible for creating green bars
                    for i in range(divisao):
                        square_x = barra_quadrado_bar[0] + i * square_width
                        square_end_x = square_x + square_width if i < 4 else barra_quadrado_bar[0] + barra_quadrado_bar[2]
#
                        cv2.rectangle(screen, (square_x, barra_quadrado_bar[1]), (square_end_x, barra_quadrado_bar[1] + barra_quadrado_bar[3]), (0, 255, 0), 2)
#
                        #cv2.putText(screen, f"{i + 1} - {square_x}{square_width} ", (square_x + 5, barra_quadrado_bar[1] + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
#
#
                    if progressBar and len(progressBar) > 0:
                        barpg_x, barpg_y, barpg_w, barpg_h = progressBar[0]
                        print("prg", barpg_w)
                        if (barpg_w >= 178) and not notification_sent:
                            print("Peixe capturado", barpg_w)
                            sendDiscordNotification("⏺️ Captured :)", 4915076)
                            fishCatch += 1
                            gui.caught_general_label.setText(f"Fish Caught: {str(fishCatch)}")
                            keyboard.release('space')
                            pydirectinput.click(x=rightClickFixPerfom[0], y=rightClickFixPerfom[1])
                            keyboard.press_and_release('z')
                            notification_sent = True  
                        if (barpg_w <= 5) and not notification_sent:
                            sendDiscordNotification("🛑 Not Captured :(", 16076880)
                            fishLost += 1
                            gui.lost_general_label.setText(f"Fish Lost: {str(fishLost)}")
                            keyboard.release('space')
                            pydirectinput.click(x=rightClickFixPerfom[0], y=rightClickFixPerfom[1])
                            keyboard.press_and_release('z')
                            notification_sent = True  
                    
                    cv2.rectangle(screen, (bar_x, bar_y), 
                                  (bar_x + bar_w, bar_y + bar_h), 
                                  (255, 0, 0), 2)
#
                    cv2.putText(screen, f"Bar (X:{bar_x}, W: {bar_w})", (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                    
                    cv2.rectangle(screen, (barpg_x, barpg_y), 
                                  (barpg_x + barpg_w, barpg_y + barpg_h), 
                                  (255, 50, 50), 2)
#
                    cv2.putText(screen, f"Progresso (X:{barpg_x}, W: {barpg_x})", (barpg_x, barpg_x - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
#
        cv2.putText(screen, f"FPS: {int(current_fps)} (barra e coluna)", (100, 200 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
#
    #
        cv2.rectangle(screen, (238, 503), 
                      (238 + 70, 503 + 13), 
                      (255, 5, 5), 2)
       
        cv2.rectangle(screen, (490, 503), 
                      (490 + 70, 503 + 13), 
                      (255, 5, 5), 2)
#
        cv2.putText(screen, f"Key L: Start", (100, 250 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
        
        cv2.putText(screen, f"Key Q: Stop", (100, 300 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
        
        cv2.rectangle(screen, (barra_quadrado_bar[0], barra_quadrado_bar[1]),
                      (barra_quadrado_bar[0] + barra_quadrado_bar[2], barra_quadrado_bar[1] + barra_quadrado_bar[3]),
                      (99, 99, 99), 2)
        
        cv2.rectangle(screen, (shake_area[0], shake_area[1]),
                      (shake_area[0] + shake_area[2], shake_area[1] + shake_area[3]),
                      (1, 99, 99), 2)
        
        cv2.rectangle(screen, (quadrado_bar[0], quadrado_bar[1]),
                      (quadrado_bar[0] + quadrado_bar[2], quadrado_bar[1] + quadrado_bar[3]),
                      (51, 153, 255), 2)
        
        cv2.rectangle(screen, (quadrado_bar_progresso[0], quadrado_bar_progresso[1]),
                      (quadrado_bar_progresso[0] + quadrado_bar_progresso[2], quadrado_bar_progresso[1] + quadrado_bar_progresso[3]),
                      (51, 153, 255), 2)
        
        cv2.imshow('Detected', screen)
        
        #elapsed_time = time.time() - start_time
        #if elapsed_time < frame_delay:
        #    time.sleep(frame_delay - elapsed_time)     

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    


    cv2.destroyAllWindows()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

