# Integrated code to control all Subsystems 1, 2, 3 and 4 whilst triggering all respective traffic light sequences.
# Created By : Malcolm Cheah, Hui Yi and Pravir
# Created Date : 21/05/2025 12:00PM
# Version = 15.2

from pymata4 import pymata4
import time

board = pymata4.Pymata4()

# Shift register control pins
dataPin = 8
latchPin = 9
clockPin = 10

# Ultrasonic sensor pins for subsystems
trigPin1, echoPin1 = 2, 3  # US1
trigPin3, echoPin3 = 6, 7  # US3
trigPin4, echoPin4 = 12, 13  # US2

# Push button pins
pb1A = 4
pb1B = 5
pa1Buzzer = 11

# Light dependant resistor pin
ldrPin = 0

# Initialize all hardware
board.set_pin_mode_digital_output(dataPin)
board.set_pin_mode_digital_output(latchPin)
board.set_pin_mode_digital_output(clockPin)

board.set_pin_mode_sonar(trigPin1, echoPin1, timeout=200000)
board.set_pin_mode_sonar(trigPin3, echoPin3)
board.set_pin_mode_sonar(trigPin4, echoPin4)

board.set_pin_mode_digital_input(pb1A)
board.set_pin_mode_digital_input(pb1B)
board.set_pin_mode_pwm_output(pa1Buzzer)
board.set_pin_mode_analog_input(ldrPin)

# LED pin for shift register indexes
tl1Green = 0 # U1pin15
tl1Yellow = 1 # U1pin1
tl1Red = 2 # U1pin2
tl2Green = 3 # U1pin3
tl2Yellow = 4 # U1pin4
tl2Red = 5 # U1in5
tl4Green = 6 # U1pin6
tl4Yellow = 7 # U1pin7
tl4Red = 8 # U1pin8
pl1AGreen = 9 # U2pin1
pl1ARed = 10 # U2pin2
pl1BGreen = 11 # U2pin4
pl1BRed = 12 # U2pin3
tl5Green = 13 # U2pin5
tl5Yellow = 14 # U2pin6
tl5Red = 15 # U2pin7
tl3Green = 16 # U3pin15
tl3Red = 17 # U3pin1
wl1A = 18 # U3pin2
wl1B = 19 # U3pin3
fl1 = 20 # U3pin4
fl2 = 21 # U3pin5
wl2A = 22 # U3pin6
wl2B = 23 # U3pin7

# ledState list for all LEDs
ledState = [0] * 24
ledChanged = False

def toggle_led():
    """
    Updates the shift register output to reflect the current LED states.
        Parameters:
            None
        Returns:
            None
    """
    global ledChanged
    if not ledChanged:
        return
    board.digital_write(latchPin, 0)
    for bit in reversed(ledState):
        board.digital_write(clockPin, 0)
        board.digital_write(dataPin, bit)
        board.digital_write(clockPin, 1)
    board.digital_write(latchPin, 1)
    ledChanged = False

def set_bits(pos, val):
    """
    Updates the 'ledState' array at the given position with the new value.
        Parameters:
            pos (int): The index of the bit to modify in ledState array
            val (int): The value to set at the specified position (0 for on and 1 for off)
        Returns:
            None
    """
    global ledChanged
    if ledState[pos] != val:
        ledState[pos] = val
        ledChanged = True

def fl_nighttime():
    """
    Activates the white LEDs to indicate nighttime conditions.
        Parameters:
            None
        Returns:
            None
    """
    set_bits(fl1, 1)
    set_bits(fl2, 1)
    toggle_led()

def fl_daytime():
    """
    Deactivates thewhite LEDs to indicate daytime conditions.
        Parameters:
            None
        Returns:
            None
    """
    set_bits(fl1, 0)
    set_bits(fl2, 0)
    toggle_led()

def smooth_distance(rawDistance, buffer):
    """
    Applies a moving average to smooth out raw distance sensor readings.
        Parameters:
            rawDistance (float): The latest distance reading from the sensor
            buffer (list of float): A list holding recent valid distance readings
        Returns:
            float or None: The smoothed distance value, or None if no valid data is available
    """
    if rawDistance is not None and rawDistance > 0:
        buffer.append(rawDistance)
        if len(buffer) > smoothingWindowSize:
            buffer.pop(0)
        return sum(buffer) / len(buffer)
    else:
        # if invalid reading, return average if available
        if len(buffer) > 0:
            return sum(buffer) / len(buffer)
        else:
            return None

def set_buzzer(freq):
    """
    Activates the buzzer with a specified frequency, if it's not already playing or if the frequency has changed.
        Parameters:
            freq (int): The frequency in Hz at which the buzzer should play
        Returns:
            None
    """
    global buzzerOn, buzzerFreq
    if not buzzerOn or buzzerFreq != freq:
        board.play_tone_continuously(pa1Buzzer, freq)
        buzzerOn = True
        buzzerFreq = freq

def stop_buzzer():
    """
    Turns off the buzzer if it is currently active.
        Parameters:
            None
        Returns:
            None
    """
    global buzzerOn, buzzerFreq
    if buzzerOn:
        board.play_tone_off(pa1Buzzer)
        buzzerOn = False
        buzzerFreq = 0

def reset_subsystem1():
    """
    Resets Subsystem 1 to its initial state.
        Parameters:
            None
        Returns:
            None
    """
    global s1Active, s1State, s1Timer, wl1FlashState
    s1Active = False
    s1State = 0
    s1Timer = 0
    wl1FlashState = 0
    set_bits(tl1Green, 1)
    set_bits(tl1Yellow, 0)
    set_bits(tl1Red, 0)
    set_bits(tl2Green, 1)
    set_bits(tl2Yellow, 0)
    set_bits(tl2Red, 0)
    set_bits(wl1A, 0)
    set_bits(wl1B, 0)

# Initialize all LEDs at initial state
set_bits(tl1Green, 1)
set_bits(tl2Green, 1)
set_bits(tl4Green, 1)
set_bits(pl1ARed, 1)   
set_bits(pl1BRed, 1)
set_bits(tl5Red, 1)  
set_bits(tl3Green, 1)
set_bits(tl3Red, 0)
set_bits(wl1A, 0)
set_bits(wl1B, 0)
set_bits(fl1, 0)
set_bits(fl2, 0)
set_bits(wl2A, 0)
set_bits(wl2B, 0)
toggle_led()

print("System ready. Monitoring...")

# State variables for Subsystem 1
s1State = 0
s1Timer = 0
s1Active = False
wl1FlashState = 0 
wl1FlashTimer = 0
wl1FlashActive = False

# State variables for Subsystem 2
s2State = 0
s2Timer = 0
s2Active = False
s2FlashState = 0
s2FlashTimer = 0
lastStatePb1A = 0
lastStatePb1B = 0
sequenceRunning = False
lastCrossingTime = 0

# State variables for Subsystem 3
s3State = 0
s3Timer = 0
s3Active = False
tl5FlashState = 0
tl5FlashTimer = 0
s3LastFlashTime = 0
s3FlashInterval = 0.5
s3FlashingOn = True

# State variables for Subsystem 4
s4State = 0
s4Active = False
wl2FlashState = 0
wl2FlashTimer = 0

# Overriding state variables for Subsystem 2
overrideSub2Overheight = False
overrideSub1BySub4 = False

# Overriding state variables for Subsystem 4
s4TriggerCount = 0
s4ClearCount = 0
s4TriggerThreshold = 8
s4ClearThreshold = 8

# Cooldown flag for Subsystem 1
s1SequenceCooldown = True

# Maximum height for overheight vehicle
maxHeight = 0.2

# Buzzer frequency constants
overrideBuzzerFrequency = 1200
normalBuzzerFrequency = 600

# Buzzer state tracking for less flicker
buzzerOn = False
buzzerFrequency = 0

# List for readings from ultrasonic sensor for smoothing 
us1Buffer = []
us2Buffer = []
us3Buffer = []
smoothingWindowSize = 5  # Number of readings to average

try:
    while True:
        now = time.time()

        rawDistanceCm1 = board.sonar_read(trigPin1)[0]
        rawDistanceCm3 = board.sonar_read(trigPin3)[0]
        rawDistanceCm4 = board.sonar_read(trigPin4)[0]

        # Smoothen readings from all ultrasonic sensors
        distanceCm1 = smooth_distance(rawDistanceCm1, us1Buffer)
        distanceCm3 = smooth_distance(rawDistanceCm3, us3Buffer)
        distanceCm4 = smooth_distance(rawDistanceCm4, us2Buffer)

        pb1AState = board.digital_read(pb1A)[0]
        pb1BState = board.digital_read(pb1B)[0]
        ldrValue = board.analog_read(ldrPin)[0]

        # Inititiate Subsytem 3 light sequence when Subsystem 1 light sequence is active
        if s1Active and not s3Active:
            if distanceCm3 is not None and 0 < distanceCm3 < 20:  
                print("Subsystem 1 active, Subsystem 3 enters new state due to US3 detection.")
                s3Active = True
                s3State = 0  
                s3Timer = now
                s3LastFlashTime = now
                s3FlashingOn = True
                s3SequenceComplete = False
                s1SequenceCooldown = True

        # Subsystem 4 debouncing and overriding logic
        if distanceCm4 is not None and 0 < distanceCm4 < (maxHeight * 100):
            s4TriggerCount += 1
            s4ClearCount = 0
        else:
            s4ClearCount += 1
            s4TriggerCount = 0

        if not overrideSub1BySub4 and s4TriggerCount >= s4TriggerThreshold:
            print("Subsystem 4 detected overheight vehicle. Overriding subsystem 1.")
            overrideSub1BySub4 = True
            wl1FlashActive = True

            # Reset Subsystem 1 when both US1 AND US3 do not detect overheight vehicle
            if (distanceCm1 is None or distanceCm1/100.0 > maxHeight) and (distanceCm3 is None or distanceCm3 >= 20):
                reset_subsystem1()

        elif overrideSub1BySub4 and s4ClearCount >= s4ClearThreshold:
            print("Subsystem 4 no longer detects overheight vehicle. Releasing override.")
            overrideSub1BySub4 = False
            wl1FlashActive = False

            # Reset Subsystem 1 when both US1 AND US3 do not detect overheight vehicle
            if (distanceCm1 is None or distanceCm1/100.0 > maxHeight) and (distanceCm3 is None or distanceCm3 >= 20):
                reset_subsystem1()

        # Determine override state 
        if distanceCm4 is not None and 0 < distanceCm4 < (maxHeight * 100):
            if not overrideSub2Overheight:
                print("Subsystem 4 detected overheight vehicle. TL4 turns RED override active.")
                overrideSub2Overheight = True
        else:
            if overrideSub2Overheight:
                print("Subsystem 4 no longer detects overheight vehicle. Releasing TL4 red override.")
                overrideSub2Overheight = False

        # Override TL4 red when US2 detects overheight vehicle
        if overrideSub2Overheight:
            set_bits(tl4Red, 1)
            set_bits(tl4Green, 0)
            set_bits(tl4Yellow, 0)

        else:
            # Only reset TL4 if subsystem2 is not active in pedestrian sequence
            if not s2Active:
                set_bits(tl4Red, 0)
                set_bits(tl4Green, 1)
                set_bits(tl4Yellow, 0)

        # Reset Subsystem 1 if US3 no longer detects an overheight vehicle
        if distanceCm3 is None or distanceCm3 > 20:
            if s3Active:
                # Ensure Subsystem 1 light sequence will run until detection of another overheight vehicle
                if s1SequenceCooldown:
                    reset_subsystem1()
                    s1SequenceCooldown = False

        # Independant light sequence of Subsystem 1
        if not overrideSub1BySub4:

            if distanceCm1 is not None and distanceCm1 > 0:
                distanceM1 = distanceCm1 / 100.0

                # Print height of overheight vehicle and currenr time to console
                if distanceM1 <= maxHeight and not s1Active:
                    heightM = 0.6 - distanceM1
                    currentTimeStr = time.strftime("%H:%M:%S on %d-%m-%Y")
                    print(f"Overheight vehicle detected! Height: {heightM:.2f} m at {currentTimeStr}")
                    s1Active = True
                    s1State = 0
                    s1Timer = now

            if s1Active:
                # Flash sequence for wl1 upon detection of overheight vehicle 
                if wl1FlashState == 0:
                    set_bits(wl1A, 1)
                    set_bits(wl1B, 0)
                    wl1FlashTimer = now
                    wl1FlashState = 1

                elif wl1FlashState == 1 and now - wl1FlashTimer >= 0.5: #wl1 shift states every 0.5 seconds
                    set_bits(wl1A, 0)
                    set_bits(wl1B, 1)
                    wl1FlashTimer = now
                    wl1FlashState = 2

                elif wl1FlashState == 2 and now - wl1FlashTimer >= 0.5:
                    wl1FlashState = 0

                set_buzzer(normalBuzzerFrequency)

                if s1State == 0 and now - s1Timer >= 0:
                    # Initiate Subsystem 1 light sequence
                    set_bits(tl1Green, 0)
                    set_bits(tl1Yellow, 1)
                    set_bits(tl2Green, 0)
                    set_bits(tl2Yellow, 0)
                    set_bits(tl1Red, 0)
                    set_bits(tl2Red, 0)
                    s1Timer = now
                    s1State += 1

                elif s1State == 1 and now - s1Timer >= 1:
                    set_bits(tl1Yellow, 0)
                    set_bits(tl1Red, 1)
                    set_bits(tl2Green, 0)
                    set_bits(tl2Yellow, 1)
                    set_bits(tl1Green, 0)
                    set_bits(tl2Red, 0)
                    s1Timer = now
                    s1State += 1

                elif s1State == 2 and now - s1Timer >= 1:
                    set_bits(tl2Yellow, 0)
                    set_bits(tl2Red, 1)
                    set_bits(tl1Green, 0)
                    set_bits(tl1Yellow, 0)
                    set_bits(tl2Green, 0)
                    set_bits(tl1Red, 1)
                    s1Timer = now
                    s1State += 1

                elif s1State == 3 and now - s1Timer >= 30:
                    distanceCm1Check = distanceCm1

                    # Check if overheight vehicle is still present
                    if distanceCm1Check is not None and distanceCm1Check / 100.0 <= maxHeight:
                        set_buzzer(2700)
                    else:
                        # Turn TL1 Green
                        set_bits(tl1Red, 0)
                        set_bits(tl1Green, 1)
                        set_bits(tl1Yellow, 0)
                        set_bits(tl2Green, 0)
                        set_bits(tl2Yellow, 0)
                        set_bits(tl2Red, 0)
                        s1Timer = now
                        s1State += 1

                elif s1State == 4 and now - s1Timer >= 1:
                    distanceCm1Check = distanceCm1

                    # Check if overheight vehicle is still present
                    if distanceCm1Check is not None and distanceCm1Check / 100.0 <= maxHeight:
                        print("Overheight vehicle still present. TL2 stays red.")
                    else:
                        # Turn TL2 Green after one second
                        set_bits(tl2Red, 0)
                        set_bits(tl2Green, 1)
                        set_bits(wl1A, 0)
                        set_bits(wl1B, 0)
                        set_bits(tl1Green, 1)
                        set_bits(tl1Yellow, 0)
                        set_bits(tl2Yellow, 0)
                        set_bits(tl1Red, 0)
                        stop_buzzer()
                        s1Active = False
                        wl1FlashState = 0
            else:
                stop_buzzer()

        else:
            set_bits(tl1Red, 1)
            set_bits(tl2Red, 1)
            set_bits(tl1Green, 0)
            set_bits(tl2Green, 0)
            set_bits(tl1Yellow, 0)
            set_bits(tl2Yellow, 0)
            set_buzzer(overrideBuzzerFrequency)

            if wl1FlashActive:
                if wl1FlashState == 0:
                    set_bits(wl1A, 1)
                    set_bits(wl1B, 0)
                    wl1FlashTimer = now
                    wl1FlashState = 1

                elif wl1FlashState == 1 and now - wl1FlashTimer >= 0.5:
                    set_bits(wl1A, 0)
                    set_bits(wl1B, 1)
                    wl1FlashTimer = now
                    wl1FlashState = 2

                elif wl1FlashState == 2 and now - wl1FlashTimer >= 0.5:
                    wl1FlashState = 0

        # Independant light sequence of Subsystem 2
        if not s2Active and not overrideSub2Overheight:
            # Initiate Subsystem 2 light sequence when pb1A or pb1B is pressed
            if not sequenceRunning and (pb1AState is not None and pb1AState == 1 and lastStatePb1A == 0):
                # Only initiate when time of last pressed is 30 seconds or more
                if now - lastCrossingTime >= 30:
                    print("Pedestrian button PB1 A pressed.")
                    s2State = 0
                    s2Active = True
                    sequenceRunning = True
                    s2Timer = now
                else:
                    print("Please wait before crossing again.")
            elif not sequenceRunning and (pb1BState is not None and pb1BState == 1 and lastStatePb1B == 0):
                if now - lastCrossingTime >= 30:
                    print("Pedestrian button PB1 B pressed.")
                    s2State = 0
                    s2Active = True
                    sequenceRunning = True
                    s2Timer = now
                else:
                    print("Please wait before crossing again.")

        if s2Active:
            if s2State == 0:
                # Initial state of pedestrian crossing
                set_bits(tl4Green, 1)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Red, 0)
                set_bits(pl1ARed, 1)
                set_bits(pl1AGreen, 0)
                set_bits(pl1BRed, 1)
                set_bits(pl1BGreen, 0)
                
                # Move to next LED configuration after 2 seconds
                if now - s2Timer >= 2:  
                    s2Timer = now
                    s2State += 1
                    
            elif s2State == 1:
                set_bits(tl4Green, 0)
                set_bits(tl4Yellow, 1)
                set_bits(tl4Red, 0)
                set_bits(pl1ARed, 1)
                set_bits(pl1AGreen, 0)
                set_bits(pl1BRed, 1)
                set_bits(pl1BGreen, 0)
                
                if now - s2Timer >= 2: 
                    s2Timer = now
                    s2State += 1
                    
            elif s2State == 2:
                set_bits(tl4Green, 0)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Red, 1)
                set_bits(pl1ARed, 0)
                set_bits(pl1AGreen, 1)
                set_bits(pl1BRed, 0)
                set_bits(pl1BGreen, 1)
                
                if now - s2Timer >= 3:  
                    s2Timer = now
                    s2State += 1
                    s2FlashState = 0  
                    
            elif s2State == 3:
                set_bits(tl4Green, 0)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Red, 1)
                set_bits(pl1AGreen, 0)
                set_bits(pl1BGreen, 0)
                
                # Flashing sequence for pl1A and pl1B
                if s2FlashState == 0:
                    set_bits(pl1ARed, 1)
                    set_bits(pl1BRed, 1)
                    if now - s2Timer >= 0.5:  # pl1 shift states every 0.5
                        s2FlashTimer = now
                        s2FlashState = 1
                elif s2FlashState == 1:
                    set_bits(pl1ARed, 0)
                    set_bits(pl1BRed, 0)
                    if now - s2FlashTimer >= 0.5:
                        s2FlashState = 0
                
                # Flashing sequence ends 2 seconds
                if now - s2Timer >= 2:
                    s2Timer = now
                    s2State += 1
                    
            elif s2State == 4:
                set_bits(tl4Green, 1)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Red, 0)
                set_bits(pl1ARed, 1)
                set_bits(pl1AGreen, 0)
                set_bits(pl1BRed, 1)
                set_bits(pl1BGreen, 0)
                
                sequenceRunning = False
                lastCrossingTime = now
                s2Active = False

        # Update last state of pedetrian button 
        if pb1AState is not None:
            lastStatePb1A = pb1AState
        if pb1BState is not None:
            lastStatePb1B = pb1BState


        # Independant light sequence of Subsystem 3
        # Detects for overheight vehicle
        if distanceCm3 is not None and 0 < distanceCm3 < 20: # Scaled height of overheight vehicle down to 20cm
            if not s3Active:
                print("Exit-Overheight Vehicle Detected in Tunnel.")
                s3Active = True
                s3State = 0  
                s3Timer = now
                s3LastFlashTime = now
                s3FlashingOn = True
                s3SequenceComplete = False
                s1SequenceCooldown = True

        # Resets Subsystem 1 if no overheight vehicle is detected
        else:
            if s3Active:
                if s3SequenceComplete or s3State == 0:  
                    print("US3 no longer detects overheight vehicle, resetting Subsystem 1 and TL5.")
                    s3Active = False
                    # Ensure Subsystem 1 light sequence will run until detection of another overheight vehicle
                    if s1SequenceCooldown:
                        reset_subsystem1()
                        s1SequenceCooldown = False

        if s3Active:
            # Check if it is nighttime or daytime to trigger flood lights
            if (distanceCm3 is not None and 0 < distanceCm3 < 20):
                if ldrValue is not None and ldrValue < 700:
                    fl_nighttime()
                else:
                    fl_daytime()
            else:
                fl_daytime()

            # Start light sequence upon detection of overheight vehicle
            if s3State == 0:
                set_bits(tl5Red, 0)
                set_bits(tl5Yellow, 1)
                set_bits(tl5Green, 0)
                s3Timer = now
                s3State = 1
                s3SequenceComplete = False
                
            elif s3State == 1:  
                if now - s3Timer >= 2:
                    set_bits(tl5Yellow, 0)
                    set_bits(tl5Green, 1)
                    set_bits(tl5Red, 0)
                    s3Timer = now
                    s3State = 2
                    
            elif s3State == 2: 
                if now - s3Timer >= 5:
                    if distanceCm3 is not None and 0 < distanceCm3 < 20:
                        s3State = 3 
                        s3LastFlashTime = now
                    else:
                        # Reset to initial state of TL5 if no overheigh vehicle is detected
                        set_bits(tl5Green, 0)
                        set_bits(tl5Red, 1)
                        set_bits(tl5Yellow, 0)
                        s3SequenceComplete = True
                        s3State = 0
                        s1SequenceCooldown = True
                        
            elif s3State == 3: 
                # Flash TL5 green if overheight vehicle is still detected
                if distanceCm3 is not None and 0 < distanceCm3 < 20: 
                    if now - s3LastFlashTime >= 0.5:
                        set_bits(tl5Green, 1 if s3FlashingOn else 0)
                        s3FlashingOn = not s3FlashingOn
                        s3LastFlashTime = now
                else:
                    # Reset to initial state of TL5 if no overheight vehicle is detected
                    set_bits(tl5Green, 0)
                    set_bits(tl5Red, 1)
                    set_bits(tl5Yellow, 0)
                    s3SequenceComplete = True
                    s1SequenceCooldown = True
                    s3State = 0

        # Independant light sequence of Subsystem 4

        # Subsystem 4 debouncing and overriding logic
        if distanceCm4 is not None and 0 < distanceCm4 < (maxHeight * 100): # Scaled height of overheight vehicle down to 20cm
            s4TriggerCount += 1
            s4ClearCount = 0
        else:
            s4ClearCount += 1
            s4TriggerCount = 0

        # Determine condition for override
        if not s4Active and s4TriggerCount >= s4TriggerThreshold:
            print("Overheight Vehicle Detected in Tunnel (Subsystem 4).")
            s4Active = True
            s4State = 0
        elif s4Active and s4ClearCount >= s4ClearThreshold:
            print("Tunnel cleared (Subsystem 4).")
            s4Active = False
            s4State = 0

        if s4Active:
            # Initiate Subsystem 4 light sequence
            if s4State == 0:
                set_bits(tl3Green, 0)
                set_bits(tl3Red, 1)
                set_bits(wl2B, 0)
                set_bits(wl2A, 0)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Green, 0)
                set_bits(tl4Red, 1)
                s4State = 1

            # Flashing sequence for wl2
            if wl2FlashState == 0:
                set_bits(wl2A, 1)
                set_bits(wl2B, 0)
                set_bits(tl3Green, 0)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Green, 0)
                set_bits(tl4Red, 1)
                wl2FlashTimer = now
                wl2FlashState = 1
            elif wl2FlashState == 1 and now - wl2FlashTimer >= 0.5: # wl2 shift states every 0.5
                set_bits(wl2A, 0)
                set_bits(wl2B, 1)
                set_bits(tl3Green, 0)
                set_bits(tl4Yellow, 0)
                set_bits(tl4Green, 0)
                set_bits(tl4Red, 1)
                wl2FlashTimer = now
                wl2FlashState = 2
            elif wl2FlashState == 2 and now - wl2FlashTimer >= 0.5:
                wl2FlashState = 0
        else:
            set_bits(tl3Red, 0)
            set_bits(tl3Green, 1)
            set_bits(wl2A, 0)
            set_bits(wl2B, 0)

        toggle_led()
        time.sleep(0.05)

except KeyboardInterrupt:
    for i in range(len(ledState)):
        set_bits(i,0)
    toggle_led()
    board.play_tone_off(pa1Buzzer)
    print("Exiting program...")
    time.sleep(1)
    board.shutdown()