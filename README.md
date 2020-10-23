# ucla-classes-spiders
Scrapy spiders to get UCLA classes information

Usage: 
scrapy crawl department-classes -o \<deptclass-filename.json> 

Change DEPARTMENT_CLASS_LOCATION in spiders/ClassDetailsSpider.py to the location of \<deptclass-filename.json>

scrapy crawl class-details -o \<class-details.json>