# Client pitch (5–7 min): Wind Forecast Monitor

**Bracketed numbers must be filled from the live January 2026 run. None are included because the app has not yet been run against real data.**

## Script
1. **Problem (1 min).** You buy power a day ahead. Every MW of wind that doesn't show up must be covered, often by costly thermal. You decide before the outcome is known, so you need to know how far to trust the wind forecast.
2. **What this does (1 min).** (a) The forecast you would actually have had at decision time, with its publish time; (b) how wrong it was across January 2026, measured with no hindsight.
3. **Demo (2 min).** Pick a delivery day and cutoff (default 09:00 the day before). Show forecast, publish time, mean/min/max, actuals overlaid. Switch to Accuracy: MAE [x] MW, bias [x] MW, P90 over-forecast [x] MW; errors by hour and horizon; worst days [x].
4. **Using it (1 min).** Take tomorrow's forecast, subtract the P90 buffer, size extra procurement to the gap; choose your own confidence with the slider.
5. **Limitations (1 min).** One month of data; buffer is indicative; cutoff time is our assumption, please confirm yours; national level, Elexon data only.
6. **Next steps.** Confirm cutoff, extend history, regional/seasonal views, connect to your procurement model.

## Slides
1. The day-ahead gap · 2. Two questions, one tool · 3. Decision-time forecast (screenshot) · 4. How accurate was January? · 5. Where errors concentrate · 6. Turning error into a buffer · 7. Limits and next steps
