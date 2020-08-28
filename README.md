# streetcred
Watching over Singapore's roads via LTA DataMaill APIs
<br><br>
LTA DataMall API: https://www.mytransport.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf

Downloads selected LTA DataMall datasets every 15 mins to Google Cloud Storage.
<br><br>
Details for the available datasets as follows:

- ### traffic-images-detections:
    - Derieved from LTA's traffic images API
    - Traffic images (from expressway cameras) are passed through an object detection model (CenterNet Resnet101 V1 FPN 512x512)
    - Top 200 detections with score > 0.2 are saved (number of detections per image can be lower than 200) 
    - Location, date and time of detection can be found in traffic-images-aggregated by joining `Filename` in `traffic-images-aggregated` to `image` in `traffic-images-detections`, for the same datetime
    - Image classes map to label can be found in `metadata` directory
    - Schema: ['image', 'class', 'score', 'x1', 'x2', 'y1', 'y2', 'relative_size']
    
- ### traffic-images-aggregated:
    - From `traffic-images-detections`, addtional filtering to obtain more reliable count of number of vehicles in feed 
    - Schema: ['CameraID', 'Latitude', 'Longitude', 'Date', 'Time', 'Filename', 'Dimensions', 'Detections']
    
- ### carpark-availability:
    - Direct from API, removed metadata to keep data concise
    - Location of carparks can be found in `metdata` directory 
    - Schema: ['AvailableLots', 'CarParkID']

- ### taxi-availability:
    - Direct from API 
    - Schema: ['Latitude', 'Longitude]

- ### traffic-incidents:
    - Direct from API 
    - Schema: ['Latitude', 'Longitude', 'Message', 'Type']
    
- ### traffic-speed-bands
    - Direct from API, remvoed metadata to keep data concinse
    - Coordinates of road stretches can be found in `metadata` directory
    - Schema: ['LinkID', 'MinimumSpeed']

<br><br>
# Downloading Data
To download data, run `download_from_gcs.py` which is found in `applications/lta`.

Enter start and end dates, comment out datasets which are not required.

<br><br>
# Contribute
Looking forward to incorporate improvements to the code, or let me know if I'm missing something out.

This currently costs abit to download, process and store the data, so I'd be more than happy to accept financial contributions. Contributions above the requirements of the current set up will go towards upgrading the instance to run the task more frequently (max once every 5 minutes, the source update frequency of the datasets here).

<br><br>
# Running the downloader on your own instance
1. Create service account. Required permissions:
    - Monitoring (https://cloud.google.com/monitoring/access-control) and storage admin

2. Create small Compute Engine instance. To manage costs, can run on preemptible instance but with additional monitoring to auto-restart instance, such as with https://github.com/aaronteoh/gcloud-monitor
Require instance specs for start-up:
    - n1-standard-1 instance (set region closet to you). Can be reduced after setup to n1 series instance with 1 vCPU and 2.25 GB memory
    - persistent disk: 10 GB might work, 20 GB should be more than sufficient
    - OS: Ubuntu
    - Assign service account
    
3. Create Google Cloud Storage bucket in region closest to you to minimize egress cost for downloads (should be same as instance)

4. SSH to instance

5. Install logging agent. Follow instructions here: https://cloud.google.com/monitoring/agent/installation

6. configure timezone

    ```
    $ sudo ln -sf /usr/share/zoneinfo/Asia/Singapore /etc/localtime
   ```
   
7. Set up Python and pip. https://cloud.google.com/python/setup
    ```
    $ sudo apt update
    $ sudo apt install python3
    $ sudo apt install python3-pip
    ```
   
8. Set up repository
    ```
    $ sudo mkdir /opt/repositories
    $ cd /opt/repositories
    $ sudo git clone https://github.com/aaronteoh/streetcred.git
    ```
   
9. Edit Google Cloud Storage paths in `datamall-realtime_data.py` and `traffic-images_detect_objects.py`

10. Install dependancies
    ```
    $ cd streetcred
    $ sudo pip3 install -r requirements.txt
    ```

11. Get LTA DataMall API key.
    
12. Add LTA DataMall API key to instance.
    ```
    $ sudo mkdir credentials
    $ cd credentials
    $ echo '<API KEY>' | sudo tee LTA-API-KEY
    ```

13. Test that everything works so far.
    ```
    $ cd /opt/repositories/streetcred
    $ sudo python3 traffic_images-download_images.py
    $ sudo python3 datamall-realtime_data.py
    ```

14. Download tensorflow models for detection script
    ```
    $ sudo git clone https://github.com/tensorflow/models.git
    $ cd models/research
    $ sudo apt  install protobuf-compiler
    $ sudo protoc object_detection/protos/*.proto --python_out=.
    $ sudo cp object_detection/packages/tf2/setup.py .
    $ sudo python3 -m pip install .
    $ sudo python3 object_detection/builders/model_builder_tf2_test.py
    ```

15. Set up GCP credentials. First, download key for service account to local. Inside ssh, click on settings button, upload file, then upload credentials file
    ```
    $ cd /home/$USER
    $ sudo mv <file name> /opt/repositories/streetcred/credentials/<file name>
    $ cd /opt/repositories/streetcred/models/research/object_detection/test_data
    $ sudo curl -O http://download.tensorflow.org/models/object_detection/tf2/20200711/centernet_resnet101_v1_fpn_512x512_coco17_tpu-8.tar.gz
    $ sudo tar -zxvf centernet_resnet101_v1_fpn_512x512_coco17_tpu-8.tar.gz
    ```

16. Test detections script.
    ```
    $ cd /opt/repositories/streetcred
    $ sudo python3 detect_objects.py
    ```

17. Set up crontab.
    ```
    $ sudo crontab /opt/repositories/streetcred/crontab
    ```

18. To save costs, can scale down instance from n1-standard-1 to n1 custom, 1 vCPU, 2.25 GB memory

### If task fails at any step without trace printed, can review logs with:
```
$ tail -f /var/log/kern.log
```