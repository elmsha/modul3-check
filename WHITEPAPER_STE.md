# Modul-3-Atlas – Technical Description

**The value of dynamic tariffs, smart control and §14a grid fees in different grid areas – a comparison of twelve distribution grid operators**

*Elmar Hackmann, Oldenburg · October 2026 · Prototype · App: [zwei-signale.streamlit.app](https://zwei-signale.streamlit.app) · Code and data: [github.com/elmsha/modul3-check](https://github.com/elmsha/modul3-check)*

> **Language:** This document uses ASD-STE100 Simplified Technical English (STE). The author wrote it to the STE rules. A checker tool did not verify it. The German original is [WHITEPAPER.md](WHITEPAPER.md).

---

## 0. Technical names and abbreviations

| Term | Meaning |
|---|---|
| Grid operator | The company that operates the local low-voltage electricity grid. |
| Grid fee | The price per kWh that the grid operator charges for the use of the grid. |
| Price sheet | The document in which the grid operator publishes the grid fees for one year. |
| §14a EnWG | The German law section for controllable loads (heat pumps, wallboxes). |
| Module 1 | A fixed decrease of the grid fee per year. |
| Module 3 | A time-variable grid fee. You can use it only together with Module 1. |
| HT | High tariff. The grid fee in the time window with the highest price. |
| ST | Standard tariff. The grid fee outside the HT and NT windows. |
| NT | Low tariff. The grid fee in the time window with the lowest price. |
| Day-ahead price | The exchange price for electricity, set one day before delivery, for each quarter-hour. |
| Dynamic tariff | An electricity tariff that uses the day-ahead price for each quarter-hour. |
| HEMS | Home energy management system. It controls when a heat pump or a wallbox uses electricity. |
| EV | Electric vehicle. |
| PV | Photovoltaic system (solar power). |
| Market fit | The correlation between the grid fee and the day-ahead price in one day. |
| Lift | How often a tariff window contains the highest or lowest day-ahead prices, divided by chance. |

---

## 1. Summary

### 1.1 Problem

Since April 2025, grid operators must offer Module 3 for heat pumps and wallboxes. Each grid operator sets its own HT and NT time windows. There is no central comparison of these designs.

### 1.2 What the Modul-3-Atlas does

The Modul-3-Atlas compares the 2026 price sheets of twelve grid operators. It examines each design in three areas:

1. **Rule compliance.** Does the design obey the BDEW guideline for Module 3?
2. **Market fit.** Does the grid fee follow the day-ahead price from October 2025 to September 2026?
3. **Customer value.** How much money does a household save per year?

### 1.3 Results for tariff providers and HEMS providers

- **The grid area sets the value.** A household with a heat pump and an EV saves 314 € to 762 € per year. The day-ahead prices are the same in all areas. Only the grid fee is different.
- **Module 3 is not always a good recommendation.** In three of twelve grid areas, Module 3 gives a commuter household almost no value. In one area, it costs more. In these areas, recommend Module 1 only.
- **Grid-aware control gives more value.** A HEMS that uses the day-ahead price and the grid fee saves 15 € to 130 € more per year. A HEMS that uses only the day-ahead price does not get this value.

### 1.4 Main findings

1. **There are two design types.** Eight of twelve grid operators put the NT window at night. Four put it fully or partly at midday. Four use HT and NT only in some seasons. Almost all put the HT window in the late afternoon and the evening.
2. **The HT window agrees with the market. The NT window often does not.** HT windows contain the highest day-ahead prices about 2.4 times more often than chance. In summer, all-year night NT windows contain almost none of the lowest day-ahead prices (lift approximately 0.1). In summer, the lowest prices occur at midday because PV systems supply much electricity.
3. **Market fit and customer value are in conflict.** A midday NT window has the best market fit. But a commuter household gets almost no value from it, because the EV is not at home at midday. A night NT window gives value to this household. But it does not agree with the market in summer.
4. **A hybrid design decreases the conflict.** A hybrid design has an NT window at night and an NT window at midday. N-ERGIE Netz uses this design. It has a medium market fit and gives value to both household types.

**Example for EWE NETZ:** Add an NT window from 11:00 to 15:00. The market fit increases from 0.27 to 0.46. The value for a commuter household increases from 101 € to 140 € per year. The value for a household with an EV at home during the day increases from 66 € to 156 € per year. The design obeys the rules.

### 1.5 Limit of the market fit

Grid operators set the time windows to agree with the load in their grid. They do not set them to agree with the market. Thus, the market fit does not show if a design is correct or incorrect. It shows if the grid fee moves flexible loads into hours with surplus electricity. In rural grids with many PV systems, a midday NT window can also decrease the grid load. Each grid operator must examine this with its own load data.

---

## 2. Background

### 2.1 §14a EnWG and the three modules

Heat pumps and wallboxes add much load to the low-voltage grid. Since 2024, §14a EnWG lets grid operators decrease the power of these loads when the grid has too much load. The decisions of the Bundesnetzagentur (BK6-22-300, BK8-22/010-A) give the details. In return, the customer pays a lower grid fee.

| Module | Content |
|---|---|
| Module 1 | Fixed decrease of the grid fee per year. This is the default. |
| Module 2 | Percentage decrease of the grid fee per kWh. It needs a separate meter. |
| Module 3 | Time-variable grid fee with HT, ST and NT. You can use it only with Module 1. It is available since 1 April 2025. |

### 2.2 Rules for Module 3

The [BDEW guideline for Module 3 (V1.2, July 2026)](https://www.bdew.de/media/documents/2026-07-17_BDEW-Anwendungshilfe_Modul-3_V1.2.pdf) gives these rules:

- The time windows and prices apply for one calendar year and for the full grid area.
- The grid operator can apply HT and NT only in some quarters. The minimum is two quarters.
- The time windows and prices are the same in all quarters with HT and NT.
- The ST is equal to the normal grid fee per kWh for households.
- The NT must be between 10 % and 40 % of the ST.
- The HT must not be more than 200 % of the ST.
- The HT window must be a minimum of two hours per day.
- The grid operator sets the windows from measured high-load and low-load times in its grid.
- The grid operator must publish the preliminary price sheet not later than 15 October for the next year.

In May 2026, the Bundesnetzagentur started enforcement procedures against two grid operators. These grid operators did not apply Module 3 correctly. The Bundesnetzagentur will start more procedures ([press release](https://bundesnetzagentur.de/SharedDocs/Pressemitteilungen/DE/2026/20260528_14a.html)).

### 2.3 Why the electricity market is important

Since October 2025, the day-ahead market sets a price for each quarter-hour. Wind and PV systems have marginal costs of almost zero. When they supply much electricity, the price decreases. Because there are more PV systems now, the lowest prices occur at midday from spring to autumn. In winter, the lowest prices occur more at night.

Since 2025, all electricity suppliers must offer a dynamic tariff (§41a EnWG). A household with a dynamic tariff and Module 3 gets two price signals at the same time. A wallbox or a heat pump can move its load only one time. If the two signals do not agree, each signal has less effect.

### 2.4 Data availability

There is no central database of Module 3 time windows. Each grid operator publishes its own price sheet, usually as a PDF file. The dena describes the data exchange for time-variable grid fees as a bottleneck ([dena 2026](https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2026/Datenraum_als_Enabler_variabler_Netzentgelte.pdf)). Consumer websites such as [14a-atlas.de](https://www.14a-atlas.de/) and [energiemarie.de](https://energiemarie.de/) show the data for households. A comparison with market data and value per grid area does not exist yet.

---

## 3. Method

### 3.1 Data

| Data | Source | Period |
|---|---|---|
| Module 3 time windows, prices, quarters | 2026 price sheets of the grid operators. Some data comes from secondary sources (refer to Section 5). | 2026 |
| Day-ahead prices DE-LU, 15 minutes | [Energy-Charts](https://api.energy-charts.info/) (Fraunhofer ISE; data Bundesnetzagentur/SMARD, CC BY 4.0) | Oct 2025 – Sep 2026 |
| Outdoor temperature Oldenburg, each hour | [Open-Meteo](https://open-meteo.com/) (CC BY 4.0) | Oct 2025 – Sep 2026 |

All grid areas use the same day-ahead prices, because they are in one bidding zone. The analysis applies the 2026 grid fees to the full period.

### 3.2 Indicators

**Rule check.** The analysis does a check of these rules:

- NT is 10 % to 40 % of ST.
- HT is not more than 200 % of ST.
- The HT window is a minimum of 2 hours per day.
- HT and NT apply in a minimum of two quarters.
- The HT window and the NT window do not overlap.

The tolerance is 0.5 percentage points. This tolerance accepts rounding errors from gross prices.

**Market fit.** For each day with HT and NT, the analysis calculates the correlation between the grid fee and the day-ahead price. It uses the 96 quarter-hours of the day. Then it calculates the mean value of all days.

- A value of +1 shows that the grid fee is high when the day-ahead price is high, and low when it is low.
- A value of 0 shows no relation.
- The analysis shows the market fit for summer (Q2, Q3) and for winter (Q1, Q4) separately.

**Lift.** For each day, the analysis finds the 25 % of quarter-hours with the highest day-ahead prices. It counts how many of them are in the HT window. Then it divides this share by the time share of the HT window. The lift for NT uses the 25 % lowest prices and the NT window. A lift of 1.0 is equal to chance.

**Customer value.** The analysis simulates a household for each quarter-hour of one year:

- Household electricity: 3,000 kWh per year. This load does not move.
- EV: 2,500 kWh per year, 11 kW charging power.
- Heat pump: 4,000 kWh per year. The heat demand comes from the outdoor temperature. The efficiency (COP) changes with the outdoor temperature. The heat pump can move 30 % of the daily heat.

The control moves the flexible loads into the quarter-hours with the lowest price. The control knows the day-ahead prices at the time of the decision. It does not know future prices that are not yet published.

The analysis compares these variants of a dynamic tariff:

| Variant | Grid fee | Control |
|---|---|---|
| B | Module 1 | No control |
| C | Module 1 | Control by the day-ahead price |
| D | Module 1 + 3 | Control by the day-ahead price only |
| E | Module 1 + 3 | Control by the day-ahead price and the grid fee |

The customer value of Module 3 is the cost difference C minus E, in euro per year, gross. The analysis uses two household profiles:

- **Commuter:** The EV is at the wallbox on workdays from 18:00 to 07:00.
- **At home:** The EV is at the wallbox almost all the time (home office, second car).

### 3.3 Value split, customer calculator and schedules

For tariff providers and HEMS providers, the analysis splits the total saving into three parts. The reference is a dynamic tariff without control and without §14a.

1. **Module 1:** the fixed decrease of the grid fee, gross.
2. **Control:** the saving from control by the day-ahead price (B to C).
3. **Module 3:** the saving from the time-variable grid fee (C to E).

The **value of grid-aware control** is D to E. In both variants, the customer uses Module 3. In D, the control knows only the day-ahead price. In E, the control knows the day-ahead price and the grid fee.

The app calculates these values for four customer types. In the customer calculator, the user can set the household data. For each grid operator, the user can download a **grid fee schedule** as a CSV file. The schedule shows the tariff stage and the grid fee for each quarter-hour of one year.

---

## 4. Results

### 4.1 Overview

| Grid operator | Design | Period | Market fit | Summer | Winter | Lift HT | Lift NT | Value commuter | Value at home |
|---|---|---|---|---|---|---|---|---|---|
| Bayernwerk Netz | Midday NT | Q2/Q3 | 0.67 | 0.67 | – | 2.5 | 3.4 | −17 € | 58 € |
| LEW Verteilnetz | Midday NT | All year | 0.52 | 0.62 | 0.42 | 2.5 | 2.3 | 1 € | 104 € |
| Avacon Netz | Night NT | Q1/Q4 | 0.50 | – | 0.50 | 2.8 | 2.0 | 161 € | 144 € |
| Netze BW | Midday NT | All year | 0.49 | 0.61 | 0.37 | 2.4 | 2.3 | 5 € | 128 € |
| E.DIS Netz | Night NT | Q1/Q4 | 0.47 | – | 0.47 | 2.2 | 2.1 | 125 € | 109 € |
| N-ERGIE Netz | Hybrid | All year | 0.43 | 0.32 | 0.54 | 2.7 | 1.4 | 147 € | 165 € |
| Schleswig-Holstein Netz | Night NT | Q1/Q4 | 0.38 | – | 0.38 | 1.5 | 1.8 | 174 € | 155 € |
| Stromnetz Berlin | Night NT | All year | 0.28 | −0.01 | 0.57 | 2.6 | 0.9 | 201 € | 139 € |
| EWE NETZ | Night NT | All year | 0.27 | −0.01 | 0.55 | 2.4 | 1.0 | 101 € | 66 € |
| wesernetz Bremen | Night NT | All year | 0.23 | −0.03 | 0.48 | 2.3 | 1.2 | 113 € | 74 € |
| Westnetz | Night NT | All year | 0.17 | −0.17 | 0.52 | 1.8 | 1.0 | 383 € | 273 € |
| SWM Infrastruktur | Night NT | All year | 0.09 | −0.22 | 0.41 | 1.1 | 1.1 | 170 € | 108 € |

All twelve designs obey the rules. Almost all grid operators set the NT at one of the two limits. Seven set it at 10 % of the ST. Four set it at 40 % of the ST. Some values are slightly above or below the limit because of rounding. These values are in the tolerance. Only Stromnetz Berlin uses a value between the limits (35 %).

### 4.2 Interpretation

- **In winter, all designs have a satisfactory market fit** (0.37 to 0.57). The evening peak and the low prices at night agree with the usual windows.
- **In summer, the designs are different.** All-year night NT windows have a market fit of approximately zero or less in summer. Seasonal designs prevent this problem. Avacon, E.DIS and SH Netz do not use Module 3 in summer. Bayernwerk uses Module 3 only in summer, with a midday NT window.
- **The price level sets most of the customer value.** Westnetz has the highest value. The cause is the high ST (9.53 ct/kWh) and the large difference between HT and NT. The window design is not the cause.
- **A midday NT window can cost a commuter more.** At Bayernwerk, a commuter household pays slightly more with Module 3. The EV cannot use the midday NT window. Part of the household load occurs in the evening HT window. This can decrease the number of customers who select Module 3.

### 4.3 Design variants for EWE NETZ

| Variant | Market fit | Summer | Winter | Value commuter | Value at home |
|---|---|---|---|---|---|
| Original (NT 23:00–05:00) | 0.27 | −0.01 | 0.55 | 101 € | 66 € |
| Add NT 12:00–14:00 | 0.38 | 0.18 | 0.58 | 125 € | 139 € |
| Add NT 11:00–15:00 | 0.46 | 0.33 | 0.59 | 140 € | 156 € |
| Only NT 11:00–15:00 | 0.50 | 0.56 | 0.45 | 4 € | 82 € |

The hybrid variant increases the market fit and the customer value at the same time. The effect on the grid is not known. Only grid load data can show if more midday load decreases or increases the load in the EWE grid. Also, a higher customer value gives lower grid fee revenue from these customers. The grid operator must recover this revenue through the other grid fees.

### 4.4 Value for tariff providers and HEMS providers

The table shows the saving per year, gross. The reference is a dynamic tariff without control and without §14a. Customer type: heat pump and commuter EV.

| Grid operator | Module 1 | Control | Module 3 | **Total** | Value of grid-aware control |
|---|---|---|---|---|---|
| Westnetz | 165 € | 213 € | 383 € | **762 €** | 130 € |
| Stromnetz Berlin | 147 € | 212 € | 201 € | **559 €** | 68 € |
| Schleswig-Holstein Netz | 137 € | 211 € | 174 € | **522 €** | 42 € |
| SWM Infrastruktur | 138 € | 211 € | 170 € | **518 €** | 41 € |
| Avacon Netz | 134 € | 211 € | 161 € | **505 €** | 37 € |
| N-ERGIE Netz | 133 € | 211 € | 147 € | **491 €** | 59 € |
| E.DIS Netz | 129 € | 210 € | 125 € | **464 €** | 34 € |
| wesernetz Bremen | 129 € | 210 € | 113 € | **452 €** | 55 € |
| EWE NETZ | 109 € | 208 € | 101 € | **418 €** | 38 € |
| Netze BW | 148 € | 212 € | 5 € | **365 €** | 35 € |
| LEW Verteilnetz | 117 € | 209 € | 1 € | **326 €** | 27 € |
| Bayernwerk Netz | 122 € | 210 € | −17 € | **314 €** | 15 € |

Total saving per customer type:

| Grid operator | Heat pump | EV (commuter) | EV (at home) | Heat pump + EV |
|---|---|---|---|---|
| Westnetz | 398 € | 533 € | 579 € | 762 € |
| Stromnetz Berlin | 306 € | 390 € | 484 € | 559 € |
| Schleswig-Holstein Netz | 310 € | 356 € | 493 € | 522 € |
| SWM Infrastruktur | 291 € | 379 € | 473 € | 518 € |
| Avacon Netz | 298 € | 346 € | 485 € | 505 € |
| N-ERGIE Netz | 276 € | 335 € | 509 € | 491 € |
| E.DIS Netz | 264 € | 325 € | 465 € | 464 € |
| wesernetz Bremen | 247 € | 333 € | 450 € | 452 € |
| EWE NETZ | 221 € | 298 € | 420 € | 418 € |
| Netze BW | 248 € | 242 € | 521 € | 365 € |
| LEW Verteilnetz | 210 € | 210 € | 469 € | 326 € |
| Bayernwerk Netz | 198 € | 223 € | 454 € | 314 € |

**How to read the tables:**

- The value of control by the day-ahead price is almost the same in all areas, because all areas use the same day-ahead prices.
- Module 1 and Module 3 cause the differences between the areas. Module 3 causes most of them.
- In areas with a midday NT window, the value depends on the EV. If the EV is at home during the day, the value is much higher. In these areas, divide your customers into commuters and customers who are at home.

**Instructions for the control logic:**

1. Calculate the total price for each quarter-hour: day-ahead price + grid fee stage + taxes and levies.
2. Use this total price for the control. Do not use only one signal.
3. For heat pumps, also use the efficiency at the outdoor temperature (price divided by COP).

**Reason:** In summer, all-year night NT windows do not contain 98 % to 100 % of the quarter-hours with the lowest day-ahead prices. At SWM Infrastruktur, the HT window is long (08:30 to 20:45). There, the day-ahead price and the grid fee give opposite signals in 18 % of all quarter-hours.

---

## 5. Limits

- **Data quality.** The author compared five price sheets with the original document. Seven come from secondary sources. For these, the author divided gross prices by 1.19. For Bayernwerk, a secondary source gave incorrect quarters. The app shows the check status for each grid operator.
- **Market fit is not the legal standard.** Grid operators set windows from their grid load. The grid load is not public. This analysis does not include it.
- **Load profiles.** The analysis uses typical load profiles, not measured data. The heat pump flexibility is an assumption. The weather data is only for Oldenburg.
- **Period.** The analysis applies the 2026 grid fees to the period October 2025 to September 2026.
- **Meter.** The analysis applies Module 3 to the full meter.
- **Missing grid operators.** The analysis does not include Hamburger Energienetze and MITNETZ. A secondary source states that they do not offer Module 3 yet. The author did not verify this.
- **No advice.** This document does not give legal advice, tariff advice or investment advice.

## 6. Next steps

1. Add the 2027 price sheets. The preliminary versions are available since 15 October 2026. Compare them with 2026.
2. Add more grid operators (30 to 50). Compare all price sheets with the original documents.
3. Add the grid view. Use PV density and feed-in profiles for each grid area. These can show if midday windows decrease the grid load.
4. Speak with tariff providers and HEMS providers. Find which grid areas they prefer, how they show savings to customers, and which data they need for their control.
5. Supply the grid fee schedules through an API. Add 2027 and more grid operators.

---

## Sources

- [BDEW guideline for Module 3, V1.2 (17 July 2026)](https://www.bdew.de/media/documents/2026-07-17_BDEW-Anwendungshilfe_Modul-3_V1.2.pdf)
- [Bundesnetzagentur: press release on §14a, 28 May 2026](https://bundesnetzagentur.de/SharedDocs/Pressemitteilungen/DE/2026/20260528_14a.html)
- [dena: Data space as enabler of variable grid fees (2026)](https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2026/Datenraum_als_Enabler_variabler_Netzentgelte.pdf)
- [ZfK: Time-variable grid fees – Module 3 in the 2026 price sheets](https://www.zfk.de/politik/regulierung/zeitvariable-netzentgelte-modul-3-netzbetreiber)
- Price sheets of the grid operators and secondary sources: refer to `netzbetreiber.json` or the tab "Daten & Fahrpläne" in the app
- [Energy-Charts API](https://api.energy-charts.info/), Fraunhofer ISE; data Bundesnetzagentur/SMARD, CC BY 4.0
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), CC BY 4.0
