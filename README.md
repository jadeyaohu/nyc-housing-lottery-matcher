# NYC Housing Lottery Matcher

Enter household size, income and wishes. The app works out the household's % of AMI (HPD 2026),
the HPD income band, and lists Housing Connect lotteries with units in that band and unit size,
the preferences that may apply (community board, disability, city employee/veteran, NYCHA, senior),
and a plain note on how many units are in your band.

- Public data only: NYC Open Data "Advertised Lotteries on Housing Connect" (By Lottery, By Building)
  and the HPD AMI table. Mini lotteries and Mitchell-Lama lotteries are not in this data.
- "Open now" uses the deadline date, not the status field (many "Active" rows are past their deadline).
- Not an eligibility decision, no log-number prediction, never applies for anyone. Applying on Housing Connect is free.

## Language
The app follows the browser language (Chinese browsers see 中文, everyone else sees English). Visitors can switch with the EN / 中文 toggle, or open the app with `?lang=zh` or `?lang=en`.

## Run
    pip install -r requirements.txt
    streamlit run app.py
    # or command line:
    python match.py --size 3 --income 85000 --units 1BR 2BR --borough BK BX

## Known limits
- The data gives units by size and by income band separately, not crossed, so a match means the
  lottery has both; check the ad for which sizes are at which income levels.
- Unit-size guide by household size is rough; each ad sets its own limits.
- ZIP -> community board is a best guess from the building file.
