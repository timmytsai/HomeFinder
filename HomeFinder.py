import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import section

requests.packages.urllib3.disable_warnings()

class HomeFinder():

	def __init__(self):
		self.config = json.load(open('config.json'))

		self.url = 'https://rent.591.com.tw/home/search/rsList?is_new_list=1&type=1&region=1&order=posttime&orderType=asc'
		self.headers = {
		    'User-Agent': 'My User Agent 1.0',
		    'Cookie': 'urlJumpIp=1'
		}

	def get_section(self, city):
		sections = None
		for k, v in self.config[city].iteritems():
			if v is True:
				if sections is None:
					sections = section.SECTION_NUM[k]
				else:
					sections += ',' + section.SECTION_NUM[k]

		return sections

	def get_rent_price(self):
		start_price = str(self.config['rent']['start_price'])
		end_price = str(self.config['rent']['end_price'])

		return start_price + ',' + end_price

	def get_area(self):
		start_area = str(self.config['area']['start_area'])
		end_area = str(self.config['area']['end_area'])

		return start_area + ',' + end_area

	def get_equipment(self):
		equipment = None
		for k, v in self.config['equipment'].iteritems():
			if v is True:
				if equipment is None:
					equipment = k
				else:
					equipment += ',' + k

		return equipment

	def get_other_condition(self):
		other = None
		for k, v in self.config['other'].iteritems():
			if v is True:
				if other is None:
					other = k
				else:
					other += ',' + k

		return other

	def get_cover(self):
		not_cover = str(self.config['not_cover'])

		return not_cover

	def build_url(self, city):
		base_url = self.url

		section = self.get_section(city)
		if section is not None:
			base_url += '&section=' + section

		price = self.get_rent_price()
		base_url += '&rentprice=' + price

		area = self.get_area()
		base_url += '&area=' + area

		other = self.get_other_condition()
		base_url += '&other=' + other

		equipment = self.get_equipment()
		base_url += '&option=' + equipment

		not_cover = self.get_cover()
		base_url += '&not_cover=' + not_cover

		return base_url

	def set_cookies(self, city):
		city_num = section.CITY_NUM[city]
		self.headers['Cookie'] = 'urlJumpIp={0}'.format(city_num)

	def diff(self, new_list, original_list):
	    second = set(original_list)
	    return [item for item in new_list if item not in original_list]

	def get_top_object_id_list(self):
		query_objects = []
		for k, v in self.config['city'].iteritems():
			if v:
				url = self.build_url(k)
				self.set_cookies(k)
				print url
				response = requests.get(url, headers=self.headers)
				raw_datas = json.loads(response.text)
				top_objects = raw_datas['data']['data']
				for house in top_objects:
					query_objects.append(str(house['post_id']))

		return query_objects


	def send_notification(self, new_objects):
		sender = self.config['smtp']['account']
		passwd = self.config['smtp']['password']
		receivers = self.config['smtp']['recipients']

		msg = MIMEMultipart()
		msg['Subject'] = "New Objects From 591!"
		msg['From'] = sender
		msg['To'] = receivers
		msg.preamble = 'Multipart massage.\n'

		smtp = smtplib.SMTP("smtp.gmail.com:587")
		smtp.ehlo()
		smtp.starttls()
		smtp.login(sender, passwd)

		content = ''
		for id in new_objects:
			url = 'https://rent.591.com.tw/rent-detail-{0}.html'.format(id)
			content += url + '\n'

		part = MIMEText(content)
		msg.attach(part)

		smtp.sendmail(msg['From'], receivers , msg.as_string())
		print 'Send mails to {0}'.format(msg['To'])

def main():
	agent = HomeFinder()
	query_objects = agent.get_top_object_id_list()

	try:
		with open('591_object_list', 'r') as file:
			content = file.read()
	except IOError:
		open('591_object_list', 'w')
		content =''

	original_objects = content.strip().split('\n')
	new_objects = agent.diff(query_objects, original_objects)
	print 'new object: {0}'.format(len(new_objects))
	
	for house_id in new_objects:
		with open('591_object_list', 'a') as file:
			file.write(house_id + '\n')

	if new_objects:
		agent.send_notification(new_objects)



if __name__ == '__main__':
	main()