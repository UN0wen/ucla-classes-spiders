import requests
from bs4 import BeautifulSoup
import json
import urllib
import scrapy
import re
headers = {
    'X-Requested-With': "XMLHttpRequest"
}

filter_flags = {
    "enrollment_status": "O,W,C,X,T,S",
    "advanced": "y",
    "meet_days": "M,T,W,R,F",
    "start_time": "8:00 am",
    "end_time": "8:00 pm",
    "meet_locations": None,
    "meet_units": None,
    "instructor": None,
    "class_career": None,
    "impacted": None,
    "enrollment_restrictions": None,
    "enforced_requisites": None,
    "individual_studies": None,
    "summer_session": None
}

DEPARTMENT_CLASS_LOCATION = "./data/S20/deptclasses_S20.json"

class ClassDetailsSpider(scrapy.Spider):
    name = "class-details"
    pattern = re.compile(r'\{.*?\}')

    def start_requests(self):
        with open(DEPARTMENT_CLASS_LOCATION, "r") as f:
            self.data = json.load(f)
            for dept in self.data:
                dept_code = dept['department']
                # if dept_code != 'COM SCI':
                #     continue
                dept_iter = iter(dept['classes'])
                class_data = []
                try:
                    next_class = next(dept_iter)
                except StopIteration:
                    continue     
                model= next_class['class_meta']
                url = self.gen_url(model)
                class_id = next_class['class_id']
                yield scrapy.Request(url=url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept_code, class_data=class_data, dept_iter=dept_iter, class_id=class_id))

    def parse(self, response, dept, class_data, dept_iter, class_id):
        # parse
        unit = response.css('.primary-row').xpath(
            '//div[@class="unitsColumn"]/p/text()').getall()
        
        try:
            unit = unit[0]
        except IndexError:
            unit = "N/A"
         
        instructor = response.css('.primary-row').xpath(
            '//div[@class="instructorColumn hide-small"]/p/text()').getall()

        try:
            instructor = instructor[0]
        except IndexError:
            instructor = "N/A"
        
        location = response.css('.primary-row').xpath(
            '//div[@class="locationColumn hide-small"]/p/text()').getall()
        
        try:
            location = location[0].strip()
        except IndexError:
            location = "N/A"

        time = response.xpath(
            '//div[contains(@class, primary-row)]/div[@class="timeColumn"]/p/text()').getall()
        
        try:
            if time[0] == "Not scheduled":
                time = time[0]
            else:
                time = time[1] + time[2]
        except IndexError:
            time = "N/A"
        
        day = response.css('.primary-row').xpath('//div[@class="dayColumn hide-small beforeCollapseHide"]/div/p/a/text()').getall()
        
        try:
            day = day[0]
        except IndexError:
            day = "N/A"
        
        d = dict(units=unit, instructor=instructor, location=location, time=time, day=day)

        class_data.append((class_id, d))
        
        try:
            next_class = next(dept_iter) 
            model= next_class['class_meta']
            url = self.gen_url(model)
            class_id = next_class['class_id']
            yield scrapy.Request(url=url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept, class_data=class_data, dept_iter=dept_iter, class_id=class_id))
        except StopIteration:
            classes = []
            for cid, cdata in class_data:
                classes.append(dict(class_id=cid, class_data=cdata))

            yield {
                "department": dept,
                "classes": classes
            }
            return

    def gen_url(self, model):
        url = "https://sa.ucla.edu/ro/Public/SOC/Results/GetCourseSummary?"
        params = {
            'model': json.dumps(model),
            "filterFlags": json.dumps(filter_flags)
        }

        params = urllib.parse.urlencode(params)
        url = url + params
        return url
