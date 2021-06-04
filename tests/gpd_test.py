MEASUREMENT_INTERVAL = 15  #24 * 60 * 60  ## seconds
GAL_PER_CUBIC_FT = 7.480543

K = 0.338   ## Flume discharge constant (varies by flume size / units)
N = 1.9     ## Discharge exponent (depends upon flume size)
## ^ These 2 constants are dependent upon Size (D) = 4-inches

def total_level_to_gpd(levels):
    ## Q = K * H^N  <-- Where H = depth at the point of measurement
    ## See: https://www.openchannelflow.com/assets/uploads/documents/Palmer-Bowlus_Flume_Users_Manual.pdf
    Q = 0.0 
    day_gallons = 0.0
    for level in levels:
        l_in_ft = level / 12.0 
        Q = K * (l_in_ft ** N)  ## Q represents free flow rate in cubic feet per second
        gal_per_interval = (Q * GAL_PER_CUBIC_FT) * MEASUREMENT_INTERVAL
        day_gallons += gal_per_interval
    print("{:.3f} gallons of flow".format(day_gallons))


# total_level = 1371.46
# total_level_to_gpd(total_level)

from sample_level_data import vals 
total_level_to_gpd(vals)


