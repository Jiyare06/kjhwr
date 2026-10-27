# Client pitch (5–7 min): Wind Forecast Monitor

All numbers below come from the live app for January 2026 delivery days. Decisions are taken at 09:00 UTC the day before delivery, ahead of the 09:50 day-ahead auction close.

## Script
1. **Problem (1 min).** You buy power a day ahead, before you know how much the wind will deliver. Every MW of wind that doesn't turn up has to be covered, often by expensive thermal generation. So the real question is how far you can trust the wind forecast you have at 09:00.

2. **What this does (1 min).** Two things:
   - **The forecast you actually had.** For any delivery day it shows the latest forecast published before your cutoff, with its publish time. Nothing published later is ever used.
   - **How wrong that forecast was.** It measures January 2026 with no hindsight: all 744 delivery hours, none missing.

3. **Demo (2 min).**
   - **15 January:** at 09:00 on the 14th, the 07:30 forecast said wind would average 11,610 MW across the day, from 8,864 to 15,834 MW. Actual wind averaged 10,584 MW.
   - **Accuracy tab, across January:**
     - The typical miss is 2,127 MW per hour (MAE; RMSE 2,606 MW). That is 22% of actual output on average.
     - **The forecast was too high in 631 of 744 hours, by 1,852 MW on average.** For a buyer this is the key point: the raw forecast is optimistic.
     - Errors were largest in the early-morning hours (about 2,500 MW MAE at 03:00–05:00 UTC). The worst days were 28, 12 and 11 January, with 4,850 to 5,330 MW average misses.
   - **Effect of waiting:** using the 09:30 forecast instead of the 07:30 one improves the typical miss by only 20 MW. It isn't worth cutting it close to the 09:50 auction close.

4. **Using it (1 min).**
   - Take tomorrow's forecast and subtract a buffer, then buy the gap.
   - At 90% confidence the January buffer is **4,306 MW**. That is 1,852 MW of consistent over-forecasting plus 2,455 MW for hour-to-hour variability.
   - On January's average this means planning on about **9,135 MW** of wind instead of the 13,433 MW forecast.
   - The slider lets you choose your own confidence level.

5. **Limitations (1 min).**
   - One month of data, so the buffer is indicative, not a guarantee.
   - The 09:00 decision time is our assumption: please confirm yours.
   - We report the over-forecasting but have not verified its cause.
   - National level, Elexon data only.

6. **Next steps.** Confirm your decision time, extend the history so the buffer is tested out-of-sample, look at whether the bias holds in calmer months, and connect the buffer to your procurement model.

## Slides
1. The day-ahead gap
2. Two questions, one tool
3. The forecast you had at 09:00 (15 Jan screenshot)
4. January accuracy: 2,127 MW typical miss, +1,852 MW bias
5. Where and when errors concentrate (by hour, by day, by lead time)
6. Turning error into a buffer (P90 = 4,306 MW)
7. Limits and next steps
