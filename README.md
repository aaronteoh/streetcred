# streetcred
Watching over Singapore's roads via LTA DataMaill APIs

Table schemas:
- traffic-images-detections: ['image', 'class', 'score', 'x1', 'x2', 'y1', 'y2', 'relative_size']
- traffic-images-aggregated: ['CameraID', 'Latitude', 'Longitude', 'Date', 'Time', 'Filename', 'Dimensions', 'Detections']
- carpark-availability: ['AvailableLots', 'CarParkID']
- taxi-availability: ['Latitude', 'Longitude]
- traffic-incidents: ['Latitude', 'Longitude', 'Message', 'Type']
- traffic-speed-bands: ['LinkID', 'MinimumSpeed']

More details at: https://www.mytransport.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf