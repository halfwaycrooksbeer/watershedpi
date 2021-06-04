from flowreport import flowreport

data = { "9/21/2020": 115.65, "9/22/2020": 451.27, "9/23/2020": 509.90 }
for date, gpd in data.items():
	flowreport.update_master_sheet_results(date, gpd)
