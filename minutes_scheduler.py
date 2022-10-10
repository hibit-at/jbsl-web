from time import sleep, time
from league_update import league_update_process

start_time = time()
print(start_time)
league_update_process()
current_time = time()
duration = current_time - start_time
print(duration)
wait_time = 300 - duration
while wait_time > 0:
    print(wait_time)
    sleep(1)
    wait_time -= 1
league_update_process()