
import os
import pycountry

directory = './'

for filename in os.listdir(directory):
    if filename.endswith(".png") and len(filename) == 6:
        country_code_2_letter = filename.split(".")[0]
        png_path = os.path.realpath(filename)
        #print(country_code_2_letter)

        for country in pycountry.countries:
            if country.alpha_2 == country_code_2_letter:
                country_code_3_letter = country.alpha_3
                print("Converting {} to {}".format(country.alpha_2, country.alpha_3))
                print("Will rename {} to {}".format(png_path,png_path.replace(country.alpha_2,country_code_3_letter ) ))

                os.rename(png_path, png_path.replace(country.alpha_2,country_code_3_letter ))
                