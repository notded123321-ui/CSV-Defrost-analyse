import csv
from datetime import datetime, timedelta
from statistics import mean

# TODO: clean this up later or make it a function maybe?
events = []
current_event = []
prev_t = None
cnt = 0

# FIXME: encoding issue happened before so keep utf-8-sig
f_name = "site_7_hp_data_all.csv"
file = open(f_name, newline="", encoding="utf-8-sig")
reader = csv.DictReader(file)

for row in reader:
    cnt = cnt + 1 # tired of cnt += 1 sometimes
    time = datetime.fromisoformat(row["timestamp"])
    
    # mode 6 is defrost according to notes from meeting
    mode_check = row["operating_mode"].strip() == "6"

    if prev_t is not None:
        diff = time - prev_t
        is_consec = (diff == timedelta(seconds=30))
    else:
        is_consec = False

    if not is_consec or not mode_check:
        if len(current_event) >= 4:
            events.append(current_event)
        current_event = []

    if mode_check:
        current_event.append(time)

    prev_t = time

    if cnt % 250000 == 0:
        print("Processed " + str(cnt) + " readings")

file.close() # manually closed bc forgot with block for a second earlier lol

if len(current_event) >= 4:
    events.append(current_event)

results = []

# intervals to check: 30s, 1m, 5m, 15m
intervals = [30, 60, 300, 900]

for i in intervals:
    pcts = []
    
    for offset in range(0, i, 30):
        obs = 0
        for ev in events:
            hit = False
            for t in ev:
                sec_val = t.hour * 3600 + t.minute * 60 + t.second
                if (sec_val - offset) % i == 0:
                    hit = True
                    break # stop inner loop once found, speeds up a tiny bit
            if hit:
                obs += 1

        if len(events) > 0:
            pct = 100 * obs / len(events)
        else:
            pct = 0
            
        pcts.append(pct)

    avg_p = mean(pcts)
    min_p = min(pcts)
    max_p = max(pcts)
    
    results.append((i, avg_p, min_p, max_p))

out_file = open("defrost_results.txt", "w")
out_file.write("Total records: " + str(cnt) + "\n")
out_file.write("Defrost events (at least 4 readings): " + str(len(events)) + "\n\n")
out_file.write("Interval | Mean % | Minimum % | Maximum %\n")

for r in results:
    iv = r[0]
    avg = r[1]
    lo = r[2]
    hi = r[3]
    out_file.write(str(iv) + " seconds | " + str(round(avg, 2)) + "% | " + str(round(lo, 2)) + "% | " + str(round(hi, 2)) + "%\n")

out_file.close()
print("Done! Created defrost_results.txt")