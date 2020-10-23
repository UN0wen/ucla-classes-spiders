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
    "advaced": "y",
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


class DepartmentClassesSpider(scrapy.Spider):
    name = "department-classes"
    pattern = re.compile(r'\{.*?\}')

    def start_requests(self):
        with open("./data/dept.json", "r") as f:
            depts = json.load(f)
            #depts = ['COM SCI']
            for dept in depts:
                dept_code = dept['value']
                #dept_code = dept
                dept_url = self.gen_url(dept_code, 1)
                yield scrapy.Request(url=dept_url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept_code, page=1, cids=[], cnames=[], cmeta=[]))

    def parse(self, response, dept, page, cids, cnames, cmeta):
        class_ids = response.xpath(
            '//div[@class="row-fluid class-title"]/@id').getall()
        class_names = response.xpath('//h3[@class="head"]/a/text()').getall()
        script_strings = response.xpath('//script/text()').getall()
        class_meta = [self.pattern.search(i).group(0) for i in script_strings]
        cmeta.extend(class_meta)
        cids.extend(class_ids)
        cnames.extend(class_names)
        if (not class_ids) or (not class_names):
            classes = []
            for id, name, meta in zip(cids, cnames, cmeta):
                classes.append(dict(class_id=id, class_name=name, class_meta=json.loads(meta)))
            
            yield {
                "department": dept,
                "classes": classes
            }
            return
        page += 1
        url = self.gen_url(dept, page)
        yield scrapy.Request(url=url, callback=self.parse, headers=headers, cb_kwargs=dict(dept=dept, page=page, cids=cids, cnames=cnames, cmeta=cmeta))

    def gen_url(self, dept, pageNum):
        url = "https://sa.ucla.edu/ro/Public/SOC/Results/CourseTitlesView?"
        params = self.gen_params(dept, pageNum)
        url = url + params
        return url

    def gen_params(self, dept, pageNum):
        model = {
            "subj_area_cd": dept,
            "search_by": "Subject",
            "term_cd": "19F",
            # "SubjectAreaName": "Computer Science (COM SCI)",
            # "CrsCatlgName": "Enter a Catalog Number or Class Title (Optional)",
            "ActiveEnrollmentFlag": "n",
            "HasData": "True"
        }

        params = {
            'search_by': 'subject',
            'model': json.dumps(model),
            'pageNumber': pageNum,
            "filterFlags": json.dumps(filter_flags)
        }

        return urllib.parse.urlencode(params)
