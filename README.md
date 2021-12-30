# Introduction

IssueFinder is a PoC web application I created as part of my summer internship at Connor Group. I received permission to include most of the source code on my personal GitHub (Microsoft and SnowFlake API credentials removed). The application won't work without these credentials and routes are configured for Mac/Windows local usage within a Docker container - so unfortunately, you won't be able to clone into this repo and try it out. 

If you'd like to see a demo of the prototype, check out this short video: https://www.loom.com/share/d09a93db4466423d9a6602b7616f4eb2

As a user, you can:

* Upload a batch of PDF files - text or image
* Enter search terms 
* View all located terms in table format (document, page num, term located) and highlighted in the original document

**Details:**

* Stack: Python/Django and Bootstrap. 
* Deployment stuff: Included are a Dockerfile/docker-compose.yml for dockerizing the application. IssueFinder is currently deployed on a virtual machine and being tested with 40+ professionals.
* Notable libraries: `PyMuPDF`, `azure.cognitiveservices.vision.computervision`, `pandas`

I contributed 100% of the code for this application on the front and back-end. Happy to talk about anything in this repo! 

# Technical details

I spent 90% of my time working on findissues/functions.py and findissues/views.py - which include all the functionality for processing and searching through the uploaded PDFs. Here's what IssueFinder does:

* Accepts two inputs: a batch of user-uploaded PDFs, and user-inputted search terms
* Uploads user-inputted search terms to a Snowflake DB for internal use
* Stores each PDF (locally, for now)
* Parses through each text PDF to locate search terms
* Interfaces with Microsoft's Computer Vision Read API to find search terms in image PDFs (more details below)
* Highlights located search terms from previous two steps in each PDF
* Outputs a summary of located terms for the user in accordion table format
* Users can click on a PDF to view/download the highlighted version with located search terms

The focus for this PoC was what I described above. IssueFinder will continue to be tested and eventually converted to an ASP.NET application by our developers for production, if approved. Hence, I did not implement models for user-uploaded data or functionality for re-using searches, etc. 

# OCR functionality

Working with the Microsoft Computer Vision Read API was enjoyable and challenging. The tricky part was figuring out how to highlight those terms in the original PDF. 

The API returned `Page` objects for each page in the uploaded PDF. Each `Page` had multiple `Line` objects, with text from each line in the PDF. The OCR quality is excellent and it was simple to determine if user search terms were in a given `Line`. 

Each `Line` has a `bounding_box` attribute with a set of coordinates that created a rectangle around the *entire* line. Here is the process I came up with for using a `bounding_box` along with `Line.text`:

* First, I had to convert the `bounding_box` values - which were in inches - to pixels, which is what `PyMuPDF` (MuPDF wrapper used for highlighting terms) uses
  * To do this, I took the dimensions of the page in pixels using PyMuPDF and created a `pixels-per-inch` conversion
* Next, I used my new `bounding_box` values to determine the `pixels-per-character` for a given `Line`
* I then took the start and stop index of the located user search term in `Line.text` 
* Using the start/stop index, I was able to create a new `modified_bounding_box` - a rectangle set of coordinates around *only* the search term, instead of the entire line
* I was then able to successfully highlight the search term in the image PDF 

The code for what I described above is found in findissues/functions.py ~lines 50 - 130

