# This software aims to help run a traffic light system, with a graphical output of data, adjustable polling times and
# a menu for these different options

# Created By : Group A17
# Date Created: 05 april 2024
# version 1.01


# IMPORTS
from pymata4 import pymata4
import matplotlib.pyplot as plot
from time import time, sleep

buttonTime = time()
pin = "1234"
buttonTally = 0
buttonState = 0
switchState = 0
interrupt = False


def callback(state):
    global buttonTally
    global buttonTime
    if time() - buttonTime > 1:
        if state[2] == 1:
            buttonTally += 1
            buttonTime = time()


def switch_callback(state):
    global switchState
    if state[2] == 1:
        switchState = 1
    else:
        switchState = 0


# GLOBAL VARIABLES
# PINS
sensorTriggerPin = 2
sensorEchoPin = 3
ser = 6
rclk = 7
srclk = 8
button = 4
slideSwitch = 5
failAlert = 9
buzzer1 = 10
buzzer2 = 11
# Side road red is going to be same as pedestrian red

board = pymata4.Pymata4()
# Set up pins
board.set_pin_mode_sonar(sensorTriggerPin, sensorEchoPin)
board.set_pin_mode_digital_output(ser)
board.set_pin_mode_digital_output(rclk)
board.set_pin_mode_digital_output(srclk)
board.set_pin_mode_digital_input(button, callback)
board.set_pin_mode_digital_input(slideSwitch, switch_callback)
board.set_pin_mode_digital_output(buzzer1)
board.set_pin_mode_digital_output(buzzer2)
board.set_pin_mode_digital_output(failAlert)
board.set_pin_mode_analog_input(0)
pollingTime = 5
pollingLists = {
    "mainRoad": [],
    "pedestrians": []
}

board.digital_write(failAlert, 1)


# FUNCTIONS

def set_lights_default(flash):
    """
    Used to set all leds off, and only control all the red lights
        parameters:
            flash (int/boolean): used to control whether the red lights are on or off
        returns:
            function has no returns
    """
    timer = time()
    stage = [0, 0, 0, flash, 0, 0, flash, 0]

    for x in stage:
        board.digital_write(ser, x)
        board.digital_write(srclk, 0)
        board.digital_write(srclk, 1)
        board.digital_write(srclk, 0)

    board.digital_write(rclk, 1)
    board.digital_write(rclk, 0)


def data_observation():

    """
        Data observation function
        receives a list or dictionary with data in the last 20 seconds
        using the data, draws a graphical representing the data

        parameters:
            no parameters required
        returns:
            function has no returns
    """
    xpoints = []
    ypoints = []
    print("1. Main Road")
    print("2. Pedestrians")
    print("3. Quit")
    data = str(input("Which road data would you like to see?: "))

    if data == "1":
        element = pollingLists["mainRoad"]
        graph = "mainRoad"
    elif data == "2":
        element = pollingLists["pedestrians"]
        graph = "pedestrians"
    elif data == "3":
        return True
    print(element)
    if len(element) < (20 / pollingTime):
        print("There is insufficient data. \nreturning to menu.")
        return True
    else:
        for item in range(1, len(element) + 1):
            xpoints.append(item * pollingTime)
            ypoint = int(element[item - 1])
            ypoints.append(ypoint)

        plot.plot(xpoints, ypoints)
        plot.xlabel("Time Elapsed (s)")
        if data == "1":
            plot.ylabel("Distance to Vehicle (cm)")
            plot.title("Distance to closest Vehicles Recorded Over Time")
        else:
            plot.ylabel("Amount of Times Button Pressed")
            plot.title("Amount of Button Presses Recorded Over Time")
        plot.savefig(f"{graph}.png")
        plot.show()


def lock_out():
    """
        lockout function, locking the user out for 2 minutes due to too many incorrect pin attempts

        parameters:
            function has no parameters
        returns:
            function has no returns
    """
    startTimer = 120
    endTimer = 0
    flash = 0
    while startTimer > endTimer:
        print("\r", f"Please wait, you are locked out for {startTimer} seconds.", end="")
        set_lights_default(flash)
        if flash == 1:
            flash = 0
        else:
            flash = 1
        startTimer -= 1
        sleep(1)


def adjustment(pollingTime):
    """
        poll time adjustment function:
        receives an input of the current poll intervals as an integer
        takes an input from the user for a new polling interval
        validates the new polling interval
        returns the new polling interval
        parameters:
            pollingTime(int) : time each of the polls is completed
        returns:
            pollingTime(int) :polling interval
            poll(int) :new polling interval
    """
    count = 0
    while True:
        askPin = input("Please enter the PIN or 'quit': ")
        if askPin == pin:
            print("Access Granted")
            break
        elif askPin == "quit":
            print("Returning to Menu")
            return pollingTime
        else:
            count += 1
            if count == 4:
                count = 0
                lock_out()
                print("\r", "Lockdown complete, you have 4 more attempts", end="\n")
            else:
                print(
                    f"Invalid PIN, please try again, you have {4 - count} "
                    f"more attempts remaining before a 2 minute lock out")
    print("Current polling time: " + str(pollingTime))
    while True:
        try:
            poll = int(input("Enter a new polling time (between 1 and 5 seconds): "))
            if 1 <= poll <= 5:
                print("New polling time set to: " + str(poll) + " returning to menu")
                return poll
            else:
                print("Invalid polling time")
        except ValueError:
            print("Invalid entry, please enter a number")


def poll_func(startTime):
    """
        polls for car distances and button presses
        :parameter:
            startTime(time): the time stage was started
        returns:
            timeTaken(time): the time it took to complete poll
            distance(int): distance to nearest car


    """
    road = board.sonar_read(sensorTriggerPin)
    pollingLists["mainRoad"].append(round(road[0], 2))
    pollTime = round(road[1] / (10 ** 9), 2)
    distance = round(road[0], 3)
    if distance >= 258:
        distance = 0
    endTime = time()
    timeTaken = (endTime - startTime) + pollTime
    return timeTaken, distance


def stage_select(num):
    """
    selects the stage and turns on leds
    :param num:(int): number of the stage
    :return: number of the stage length
    """
    if num == 1:
        stage = [0, 0, 1, 0, 0, 0, 0, 1]
        return 30, 1, stage
    elif num == 2:
        stage = [0, 0, 1, 0, 0, 0, 1, 0]
        return 3, 2, stage
    elif num == 3:
        stage = [0, 0, 1, 0, 0, 1, 0, 0]
        return 3, 3, stage
    elif num == 4:
        stage = [0, 1, 0, 0, 1, 1, 0, 0]
        return 30, 4, stage
    elif num == 5:
        pedTime = time()
        flashTime = time()
        flash = 1
        stage = [0, flash, 0, 1, 0, 1, 0, 0]
        while time() - pedTime < 3:
            for x in stage:
                board.digital_write(ser, x)
                board.digital_write(srclk, 0)
                board.digital_write(srclk, 1)
                board.digital_write(srclk, 0)

            board.digital_write(rclk, 1)
            board.digital_write(rclk, 0)
            flashTime = time()
            if flash == 1:
                flash = 0
            else:
                flash = 1
            sleep(0.5)

        return 0, 5, stage
    elif num == 6:
        stage = [0, 0, 1, 0, 0, 1, 0, 0]
        return 3, 6, stage


def stage_function(stageTime, startTime, stage, lights):
    """
    stageFunction takes a stage time and start time and uses them to add values to dictionaries for the graph
    :param lights: for shift register list
    :param stage: what stage the solution is currently in
    :param stageTime: time stage started
    :param startTime: time loop started
    :return: None
    """
    pollLoop = 0
    timeTaken = 0
    global switchState
    global buttonTally
    for x in lights:
        board.digital_write(ser, x)
        board.digital_write(srclk, 0)
        board.digital_write(srclk, 1)
        board.digital_write(srclk, 0)

    board.digital_write(rclk, 0)
    board.digital_write(rclk, 1)
    board.digital_write(rclk, 0)
    while True:
        loopTime = time()
        if switchState == 1:
            print("Interrupt Switch is Active")
            return True

        if loopTime > startTime + (pollLoop * pollingTime) + timeTaken:
            timeTaken, distance = poll_func(time())
            print(
                f"Poll took {round(timeTaken, 2)} seconds to complete \nDistance to nearest vehicle is {distance} cm\n")
            print(f"")
            if distance - pollingLists["mainRoad"][-1] > 10:
                print("Distance Rate Of Change Alert \n")
            if stage == 2 or 5:
                if distance < 10:
                    stageTime += 3
            if stage == 1:
                if distance == pollingLists["mainRoad"][-1]:
                    print("Vehicle hasn't moved on main road")

            pollingLists["mainRoad"].append(distance)
            pollLoop += 1
            if len(pollingLists["mainRoad"]) > 20 / pollingTime:
                pollingLists["mainRoad"].pop(0)
        if time() > stageTime + startTime:
            return False


def normal_operation():
    """
        normal operation of traffic lights with stages
        parameters: none
        returns:
            True

    """
    try:
        while True:
            global buttonTally
            pollingLists["pedestrians"].append(buttonTally)
            print(buttonTally)
            buttonTally = 0
            stageTime, stage, lights = stage_select(1)

            print("Stage 1")
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True

            stageTime, stage, lights = stage_select(2)
            print("Stage 2")
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True

            print(f"Pedestrian button has been pressed {buttonTally} times")
            stageTime, stage, lights = stage_select(3)
            print("Stage 3")
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True

            stageTime, stage, lights = stage_select(4)
            print("Stage 4")
            board.digital_write(buzzer1, 1)
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True

            stageTime, stage, lights = stage_select(5)
            board.digital_write(buzzer1, 0)
            print("Stage 5")
            board.digital_write(buzzer2, 1)
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True

            stageTime, stage, lights = stage_select(6)
            board.digital_write(buzzer2, 0)
            print("Stage 6")
            interrupt = stage_function(stageTime, time(), stage, lights)
            if interrupt is True:
                return True
    except KeyboardInterrupt:
        return True


# BODY
while True:
    set_lights_default(1)
    print("MENU \n Please Select One Option:")
    print("1. Normal Operation")
    print("2. Data Observation")
    print("3. Adjustment")
    print("4. Quit")
    try:
        while True:
            choice = int(input("Enter Option Number: "))
            if choice == 1:
                out = normal_operation()
                if out is True:
                    break
            elif choice == 2:
                data_observation()
                break
            elif choice == 3:
                pollingTime = adjustment(pollingTime)
                break
            elif choice == 4:
                print("Quiting Program ... ")
                quit = True
                break
            else:
                print("Invalid Option, Enter a Valid Number")
    except ValueError:
        if out is not True:
            print("Invalid Value, Enter a Number")
    if quit is True:
        set_lights_default(0)
        board.shutdown()
        break
