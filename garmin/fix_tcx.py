import datetime
import logging
import os
import xml.etree.ElementTree as ET
import argparse


# Set up logging
log = logging.getLogger()
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

def get_datetime_obj(text):
  return datetime.datetime.strptime(text, "%Y-%m-%dT%X.%fZ")

def convert_ts_to_text(ts):
  return ts.strftime("%Y-%m-%dT%X.%fZ")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--filename", help="/path/to/the/file to process")
  parser.add_argument("--output", help="/path/to/the/output/folder ")
  args = parser.parse_args()

  # Raise exception if no input files was provided
  if args.filename is None:
    raise Exception("No file provided")

  # If user does not provide an output folder, use the same as where the file to process is located
  output = os.path.dirname(args.filename) if args.output is None else args.output
  output_filename = ("%s/fixed_%s") % (output, os.path.basename(args.filename),)

  correct_start = None
  wrong_start = None

  # Register namespaces
  namespaces = {
    '': 'http://www.garmin.com/xmlschemas/UserProfile/v2',
    '': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
    '': 'http://www.garmin.com/xmlschemas/ProfileExtension/v1',
    '': 'http://www.garmin.com/xmlschemas/ActivityGoals/v1',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    '': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
  }

  for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)

  tree = ET.parse(args.filename)
  root = tree.getroot()
  for child in root:
    if child.tag == "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activities":
      for el in child:
        if el.tag == "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activity":
          count = 0
          id = el.find('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Id')
          lap = el.find('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Lap')
          correct_start = get_datetime_obj(id.text)
          wrong_start = get_datetime_obj(lap.get('StartTime'))
          lap.set('StartTime', convert_ts_to_text(correct_start))
          for track in lap.findall('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Track'):
            for track_point in track.findall('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Trackpoint'):
              for time_point in track_point.findall('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Time'):
                local_time = get_datetime_obj(time_point.text)
                correct_time = correct_start + (local_time - wrong_start)
                time_point.text = convert_ts_to_text(correct_time)


  tree.write(output_filename, encoding="UTF-8", xml_declaration=True, default_namespace="")
