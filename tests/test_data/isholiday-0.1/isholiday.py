import datetime


def getholidays(year):
    """Return a set public holidays in CZ as (day, month) tuples."""

    holidays = {
        (1, 1),  # Novy rok
        (1, 5),  # Svatek prace
        (8, 5),  # Den vitezstvi
        (5, 7),  # Cyril a Metodej
        (6, 7),  # Jan Hus
        (28, 9),  # Den Ceske statnosti
        (28, 10),  # Vznik CS statu
        (17, 11),  # Den boje za svobodu a dem.
        (24, 12),  # Stedry den
        (25, 12),  # 1. svatek Vanocni
        (26, 12),  # 2. svatek Vanocni
    }

    # Easter holiday LUT source
    # http://www.whyeaster.com/customs/dateofeaster.shtml
    easterlut = [(4, 14), (4, 3), (3, 23), (4, 11), (3, 31), (4, 18), (4, 8),
                 (3, 28), (4, 16), (4, 5), (3, 25), (4, 13), (4, 2), (3, 22),
                 (4, 10), (3, 30), (4, 17), (4, 7), (3, 27)]
    easterday = datetime.date(year, *easterlut[year % 19])
    easterday += datetime.timedelta(6 - easterday.weekday())
    # print("Easter Sunday is on ", easterday)
    holidays.update(((d.day, d.month) for d in [easterday - datetime.timedelta(2),
                                                easterday + datetime.timedelta(1)]))
    return holidays


def isholiday(date):
    return (date.day, date.month) in getholidays(date.year)


if __name__ == "__main__":
    for y in range(2016, 2025):
        print("{}: {}".format(y, getholidays(y)))
    testdates = [(2016, 3, 28), (2017, 3, 28), (2017, 4, 14)]
    for date in testdates:
        d = datetime.date(*date)
        print(d.ctime(), isholiday(d))
