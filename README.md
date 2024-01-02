A python script for scraping courses student profiles

Required arguments are:

-cookie (your own cookie, find it by right clicking >> Inspect >> Storage >> Cookies >> courses >> MoodleSession Value, on firefox)

-lower (lower bound of user indexes - inclusive)

-upper (upper bound of user indexes - inclusive)

When run it adds data in the format of ["ID", "URL", "Name", "Email", "LastAccess", "Courses"] to a .CSV file in the same directory
