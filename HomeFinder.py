import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

requests.packages.urllib3.disable_warnings()

SECTION_NUM = {
	"Zhongzheng": "1",
	"Datong": "2",
	"Zhongshan": "3",
	"Songshan": "4",
	"Daan": "5",
	"Wanhua": "6",	
	"Xinyi": "7",
	"Shilin": "8",
	"Beitou": "9",
	"Neihu": "10",
	"Nangang": "11",
	"Wenshan": "12"
}

class HomeFinder():

	def __init__(self):
		self.config = json.load(open('config.json'))

	def get_section(self):
		section = None
		for k, v in self.config['section'].iteritems():
			if v is True:
				if section is None:
					section = SECTION_NUM[k]
				else:
					section += ',' + SECTION_NUM[k]

		return section

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


	def build_url(self):
		url = 'https://rent.591.com.tw/home/search/rsList?is_new_list=1&type=1&region=1&order=posttime&orderType=asc'

		section = self.get_section()
		if section is not None:
			url += '&section=' + section

		price = self.get_rent_price()
		url += '&rentprice=' + price

		area = self.get_area()
		url += '&area=' + area

		other = self.get_other_condition()
		url += '&other=' + other

		equipment = self.get_equipment()
		url += '&option=' + equipment

		not_cover = self.get_cover()
		url += '&not_cover=' + not_cover

		return url

	def diff(self, new_list, original_list):
	    second = set(original_list)
	    return [item for item in new_list if item not in original_list]

	def get_top_object_id_list(self):
		url = self.build_url()
		headers = {
		    'User-Agent': 'My User Agent 1.0',
		}
		response = requests.get(url, headers=headers)
		raw_datas = json.loads(response.text)
		top_objects = raw_datas['data']['data']
		query_objects = []
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

	with open('591_object_list', 'r') as file:
		content = file.read()

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