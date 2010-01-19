#! /usr/bin/env python

from modifiedtestcase import *
import random

# http://www.ee.washington.edu/research/pstca/rts/rts96/

weekly = [86.2, 90.0, 87.8, 83.4, 88.0, 84.1, 83.2, 80.6, 74.0, 73.7, 71.5, 72.7, 70.4, 75.0, 72.1, 80.0, 75.4, 83.7, 87.0, 88.0, 85.6, 81.1, 90.0, 88.7, 89.6, 86.1, 75.5, 81.6, 80.1, 88.0, 72.2, 77.6, 80.0, 72.9, 72.6, 70.5, 78.0, 69.5, 72.4, 72.4, 74.3, 74.4, 80.0, 88.1, 88.5, 90.9, 94.0, 89.0, 94.2, 97.0, 100.0, 95.2]

daily = dict(
    Monday    =  93,
    Tuesday   = 100,
    Wednesday =  98,
    Thursday  =  96,
    Friday    =  94,
    Saturday  =  77,
    Sunday    =  75)

def weekend(day):
    return day == "Saturday" or day == "Sunday"

def weekday(day):
    return not weekend(day)

def summer(week):
    return 17 <= week <= 29

def winter(week):
    return 0 <= week <= 7 or 43 <= week <= 51

def spring(week):
    return 8 <= week <= 16

def autumn(week):
    return 30 <= week <= 42

def weektype(day):
    if weekend(day): return "weekend"
    if weekday(day): return "weekday"
    assert False

def season(week):
    if spring(week): return "spring"
    if summer(week): return "summer"
    if autumn(week): return "autumn"
    if winter(week): return "winter"
    assert False

hourly_winter = dict(
    weekday = [67, 63, 60, 59, 59, 60, 74, 86, 95, 96, 96, 95, 95, 95, 93, 94, 99, 100, 100, 96, 91, 83, 73, 63],
    weekend = [78, 72, 68, 66, 64, 65, 66, 70, 80, 88, 90, 91, 90, 88, 87, 87, 91, 100, 99, 97, 94, 92, 87, 81])

hourly_summer = dict(
    weekday = [64, 60, 58, 56, 56, 58, 64, 76, 87, 95, 99, 100, 99, 100, 100, 97, 96, 96, 93, 92, 92, 93, 87, 72], 
    weekend = [74, 70, 66, 65, 64, 62, 62, 66, 81, 86, 91, 93, 93, 92, 91, 91, 92, 94, 95, 95, 100, 93, 88, 80])

hourly_spring = dict(
    weekday = [63, 62, 60, 58, 59, 65, 72, 85, 95, 99, 100, 99, 93, 92, 90, 88, 90, 92, 96, 98, 96, 90, 80, 70],
    weekend = [75, 73, 69, 66, 65, 65, 68, 74, 83, 89, 92, 94, 91, 90, 90, 86, 85, 88, 92, 100, 97, 95, 90, 85])

hourly_autumn = hourly_spring

# hourly[0] is midnight till 1am, hourly[23] is 11pm till midnight
# hourly[spring][weekend][0]
hourly = dict(
    spring = hourly_spring,
    summer = hourly_summer,
    autumn = hourly_autumn,
    winter = hourly_winter)

def forecast_load(week, day, hour):
    """returns the peak load as a percentage of annual value"""
    assert 0 <= week <= 51
    assert 0 <= hour <= 23
    m1 = weekly[week] 
    m2 = daily[day]
    m3 = hourly[season(week)][weektype(day)][hour]
    m = (m1 * m2 * m3) / (100.0 * 100.0 * 100.0)
    # print m1, m2, m3, m 
    return m

def actual_load(week, day, hour):
    mu = forecast_load(week, day, hour)
    sigma = mu * 0.05
    load_level = random.normalvariate(mu, sigma)
    return load_level

def actual_load2(forecast):
    mu = forecast
    sigma = mu * 0.05
    load_level = random.normalvariate(mu, sigma)
    return load_level

# randint(self, a, b)  Return random integer in range [a, b], including both end points.

def random_day():
    return random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

def random_week():
    return random.randint(0,51)

def random_hour():
    return random.randint(0,23)

def random_bus_forecast():
    return forecast_load(random_week(),random_day(),random_hour())

def examples():
    def inner(forecast):
        print "forecast", forecast
        for x in range(10):
            print "actual", x, "=", actual_load2(forecast)
        print 
    inner(forecast_load(0, "Monday", 0))
    inner(forecast_load(0, "Sunday", 0))
    inner(forecast_load(51, "Sunday", 23))
    inner(forecast_load(37, "Tuesday", 12))
    inner(forecast_load(37, "Sunday", 5)) # probably lowest
    inner(forecast_load(50, "Tuesday", 17)) # probably highest

    for x in range(3):
        inner(forecast_load(random_week(),random_day(),random_hour()))
    
    print "-----"
    act = [forecast_load(random_week(),random_day(),random_hour()) for x in range(10000)]
    print "Random Forecast"
    print "min =", min(act), "avg =", sum(act) / len(act), "max =", max(act), "len =", len(act) 
    print act[:20]

    print "-----"
    act = [actual_load(random_week(),random_day(),random_hour()) for x in range(10000)]
    print "Random Actual"
    print "min =", min(act), "avg =", sum(act) / len(act), "max =", max(act), "len =", len(act) 
    print act[:20]

    print "-----"
    act = [actual_load2(1.0) for x in range(10000)]
    print "Normal Distribution"
    print "min =", min(act), "avg =", sum(act) / len(act), "max =", max(act), "len =", len(act) 
    print act[:20]

    print "-----"


class Tester_Weekstuff(ModifiedTestCase):
    def test_weektype(self):
        for x in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            self.assertEqual(weektype(x), "weekday")
            self.assertEqual(weekday(x), True)
            self.assertEqual(weekend(x), False)

        for x in ["Saturday", "Sunday"]:
            self.assertEqual(weektype(x),"weekend")
            self.assertEqual(weekday(x), False)
            self.assertEqual(weekend(x), True)

    def test_season(self):
        for x in range(0,7+1):
            self.assertEqual(season(x),"winter")
            self.assertEqual(spring(x), False)
            self.assertEqual(summer(x), False)
            self.assertEqual(autumn(x), False)
            self.assertEqual(winter(x), True)
        for x in range(8,16+1):
            self.assertEqual(season(x),"spring")
            self.assertEqual(spring(x), True)
            self.assertEqual(summer(x), False)
            self.assertEqual(autumn(x), False)
            self.assertEqual(winter(x), False)
        for x in range(17,29+1):
            self.assertEqual(season(x),"summer")
            self.assertEqual(spring(x), False)
            self.assertEqual(summer(x), True)
            self.assertEqual(autumn(x), False)
            self.assertEqual(winter(x), False)
        for x in range(30,42+1):
            self.assertEqual(season(x),"autumn")
            self.assertEqual(spring(x), False)
            self.assertEqual(summer(x), False)
            self.assertEqual(autumn(x), True)
            self.assertEqual(winter(x), False)
        for x in range(43,51+1):
            self.assertEqual(season(x),"winter")
            self.assertEqual(spring(x), False)
            self.assertEqual(summer(x), False)
            self.assertEqual(autumn(x), False)
            self.assertEqual(winter(x), True)

    def test_peak_load(self):
        self.assertAlmostEqual(forecast_load(0, "Monday", 0), 0.537, 3)
        self.assertAlmostEqual(forecast_load(0, "Sunday", 0), 0.504, 3)
        self.assertAlmostEqual(forecast_load(51, "Sunday", 23), 0.578, 3)
        self.assertAlmostEqual(forecast_load(37, "Tuesday", 12), 0.646, 3)

if __name__ == '__main__':
    examples()
    unittest.main()
