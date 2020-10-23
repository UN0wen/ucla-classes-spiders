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

DEPARTMENT_CLASS_LOCATION = "./data/W20/deptclasses_W20.json"

class DiscussionDetailsSpider(scrapy.Spider):
    name = "discussion-details"
    pattern = re.compile(r'\{.*?\}')

    def start_requests(self):
        with open(DEPARTMENT_CLASS_LOCATION, "r") as f:
            self.data = json.load(f)
            for dept in self.data:
                dept_code = dept['department']
                if dept_code != 'COM SCI':
                    continue
                dept_iter = iter(dept['classes'])
                class_data = []
                try:
                    next_class = next(dept_iter)
                except StopIteration:
                    continue     
                model= next_class['class_meta']
                url = self.gen_base_url(model)
                class_id = next_class['class_id']
                yield scrapy.Request(url=url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept_code, class_data=class_data, dept_iter=dept_iter, class_id=class_id, model=model))

    def class_start(self, response, model, current_section = 1, num_sections = 0, root=True, discussions=[]):
        has_discussion = 1
        if root:
            num_sections = len(response.css('.primary-row').getall())
            print(num_sections)
            has_discussion = len(response.xpath('//div[@class="enrollColumn"]/div[@class="toggle"]').getall())
            #TODO: Parse PATH value for each discussion(replace current_section/num_section) to use for model
        else:
            # Parse disc response
            disc_locations = response.xpath('//div[@class="locationColumn hide-small"]/p/text()').getall()
            d = dict(section=current_section, discussion_locations=disc_locations)
            discussions.append(d)

        if has_discussion:
            if current_section <= num_sections:
                url = self.gen_disc_url(model, current_section)
                current_section += 1
                yield scrapy.Request(url=url, callback=self.class_start, headers=headers, cb_kwargs=dict(model=model, current_section=current_section, section_count=section_count, root=False, discussions=discussions))
        
        return discussions

    

    def parse(self, response, dept, class_data, dept_iter, class_id, model={}):
        # parse
        num_sections = len(response.css('.primary-row').getall())
        class_sections = self.class_start(response, model, num_sections=num_sections)
        class_data.append((class_id, class_sections))
        
        try:
            next_class = next(dept_iter) 
            model= next_class['class_meta']
            url = self.gen_base_url(model)
            class_id = next_class['class_id']
            yield scrapy.Request(url=url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept, class_data=class_data, dept_iter=dept_iter, class_id=class_id, model=model))
        except StopIteration:
            classes = []
            for cid, csections in class_data:
                classes.append(dict(class_id=cid,  class_sections=csections))

            yield {
                "department": dept,
                "classes": classes
            }
            return

    def gen_base_url(self, model):
        url = "https://sa.ucla.edu/ro/Public/SOC/Results/GetCourseSummary?"
        model['isRoot'] = True
        params = {
            'model': json.dumps(model),
            "filterFlags": json.dumps(filter_flags)
        }

        params = urllib.parse.urlencode(params)
        url = url + params
        return url

    #TODO: secNum => PATH
    def gen_disc_url(self, model, secNum):
        url = "https://sa.ucla.edu/ro/Public/SOC/Results/GetCourseSummary?"
        model['isRoot'] = False
        model['SequenceNumber'] = secNum
        params = {
            'model': json.dumps(model),
            "filterFlags": json.dumps(filter_flags)
        }

        params = urllib.parse.urlencode(params)
        url = url + params
        return url