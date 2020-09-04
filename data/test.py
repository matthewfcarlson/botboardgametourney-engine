done = False
while (not done):
    line = input()
    if line is None:
        log("Waiting")
        sleep(1)
        continue
    log(f"Got [{line}]")
    if line.endswith("done"):
        print("Thanks for playing")
        done = True