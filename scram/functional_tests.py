from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import unittest


class HomePageTest(unittest.TestCase):

	def setUp(self):
		options = Options()
		options.headless = True
		self.browser = webdriver.Firefox(options=options)

	def tearDown(self):
		self.browser.quit()

	def test_viewing_the_home_page(self):
		# Go to the homepage
		self.browser.get('http://localhost:8000')

		# Make sure the title is correct
		self.assertIn('SCRAM', self.browser.title)


if __name__ == "__main__":
	unittest.main(warnings='ignore')