#!/usr/bin/python
# ------------------
# Pillbox Xpath script that extracts raw data from XML to yield:
#    1. Rows array, with one row object per product code. 
#    2. Ingredients array, with one object per ingredient
# ------------------
# Requirements: Python 2.6 or greater 

import os, sys, time
import StringIO
from lxml import etree
from itertools import groupby

# Check all XMLs against form codes, discard all XMLs that don't match
codeChecks = [
	"C25158", "C42895", "C42896",
	"C42917", "C42902", "C42904",
	"C42916", "C42928", "C42936",
	"C42954", "C42998", "C42893",
	"C42897", "C60997", "C42905",
	"C42997", "C42910", "C42927",
	"C42931", "C42930", "C61004",
	"C61005", "C42964", "C42963",
	"C42999", "C61006", "C42985",
	"C42992"
	]

print "processing XML with XPATH..."

def parseData(name):

	# Iterparse function that clears the memory each time it finishes running
	def getelements(filename, tag, medicineCheck):
		context = iter(etree.iterparse(filename, events=('start', 'end')))
		_, root = next(context) # get root element
		for event, elem in context:
			# If we pass "yes" via medicineCheck, then we need to return <manufacturedMedicine> instead of <manufacturedProduct> 
			if medicineCheck == 'yes':
				if event == 'end' and elem.tag == "{urn:hl7-org:v3}manufacturedMedicine":
					yield elem
				elif event == 'end' and elem.tag == '{urn:hl7-org:v3}manufacturedProduct' or elem.tag =='manufacturedProduct':
					yield elem
			else:
				if event == 'end' and elem.tag == tag:
					yield elem
		root.clear() # preserve memory

	# ------------------
	# Build SetInfo array
	# ------------------
	setInfo = {}
	setInfo['file_name'] = name
	setInfo['date_created'] = time.strftime("%d/%m/%Y")
	for parent in getelements(name, "{urn:hl7-org:v3}document", 'no'):
		for child in parent.iterchildren('{urn:hl7-org:v3}id'):
			setInfo['id_root'] = child.get('root')
		for child in parent.iterchildren('{urn:hl7-org:v3}setId'):
			setInfo['setid'] = child.get('root')
		for child in parent.iterchildren('{urn:hl7-org:v3}effectiveTime'):
			setInfo['effective_time'] = child.get('value')
		for child in parent.iterchildren('{urn:hl7-org:v3}code'):
			setInfo['document_type'] = child.get('code')

	# --------------------
	# Build Sponsors Array
	# --------------------
	sponsors ={}
	for parent in getelements(name, "{urn:hl7-org:v3}author", 'no'):
		for child in parent.iter('{urn:hl7-org:v3}representedOrganization'):
			for grandChild in child.iterchildren('{urn:hl7-org:v3}name'):
				sponsors['name'] = grandChild.text
				sponsors['sponsor_type'] = 'labler'
				grandChild.clear()

	for parent in getelements(name, "{urn:hl7-org:v3}legalAuthenticator", 'no'):
		for child in parent.iter('{urn:hl7-org:v3}representedOrganization'):
			for grandChild in child.iterchildren('{urn:hl7-org:v3}name'):
				sponsors['name'] = grandChild.text
				sponsors['sponsor_type'] = 'legal'
				grandChild.clear()

	# -----------------------------------------
	# Build ProdMedicine and Ingredients arrays
	# -----------------------------------------
	prodMedicines = []
	ingredients = []
	formCodes = []
	names = []
	# info object, which will later be appended to prodMedicines array
	info = {}
	info['SPLCOLOR']  = []
	info['SPLIMPRINT'] = []
	info['SPLSHAPE'] = []
	info['SPLSIZE'] = []
	info['SPLSCORE']  = []
	info['SPLCOATING']  = []
	info['SPLSYMBOL']  = []
	info['SPLFLAVOR']  = []
	info['SPLIMAGE']  = []
	info['IMAGE_SOURCE'] = []
	info['SPL_INGREDIENTS'] = []
	info['SPL_INACTIVE_ING'] = []
	info['SPLCONTAINS'] = []
	info['APPROVAL_CODE'] = []
	info['MARKETING_ACT_CODE'] = []
	info['DEA_SCHEDULE_CODE'] = []
	info['DEA_SCHEDULE_NAME'] = []
	info['equal_product_code'] = []
	info['NDC'] = []
	info['SPLUSE'] = []

	# substanceCodes will be filled with ingredient codes to check for duplicate ingredients
	substanceCodes = []
	# doses will be filled with ingredient numerator values to check for duplicate ingredients
	doses = []
	# codes stores product_codes, to determine how many unique products \to output with len(codes)
	codes = []
	
	for parent in getelements(name, "{urn:hl7-org:v3}manufacturedProduct", 'yes'):
		# There are <manufacturedProduct> elements that have no content and would result
		# in empty objects being appended to ingredients array. So use ingredientTrue to test.
		ingredientTrue = 0
		active = []
		inactive = []
		equalProdCodes = ''
		# Get equal product code from <definingMaterialKind>
		try:
			equalProdParent = parent.xpath(".//*[local-name() = 'definingMaterialKind']")
			for child in equalProdParent[0].iterchildren(): 
				if child.get('code') not in equalProdCodes:
					equalProdCodes = child.get('code')
		except: 
			equalProdCodes = ''
		# Get code, name and formCode for each manufacturedProduct
		# To do: Abstract the three for loops below into a function
		for child in parent.iterchildren('{urn:hl7-org:v3}code'):
			# Send product_code to codes array so we can know how many product arrays to output with len(codes)
			codes.append(child.get('code'))
		for child in parent.iterchildren('{urn:hl7-org:v3}name'):
			names.append(child.text)
		for child in parent.iterchildren('{urn:hl7-org:v3}formCode'):
			# Check to see if code in codeChecks array
			if child.get('code') not in codeChecks:
				# Exit function and move onto next XML within master.py if code not in codeCheck array
				sys.exit("Not OSDF")
			else:
				formCodes.append(child.get('code'))
		# Send code, name and formCode to info = {}
		info['product_code'] = codes
		info['product_name'] = names
		info['form_code'] = formCodes
		

		# Get <containerPackagedProduct> information
		packageProducts = []
		for child in parent.xpath("./*[local-name() = 'asContent']"):
			# Check if we're working with <containerPackagedProduct> or <containerPackagedMedicine>
			checkMedicine =  child.xpath("./*[local-name() = 'containerPackagedMedicine']")
			checkProduct =  child.xpath("./*[local-name() = 'containerPackagedProduct']")
			if len(checkProduct) != 0:
				productType = 'containerPackagedProduct'
			else:
				productType = 'containerPackagedMedicine'
			# Send product 
			for grandChild in child.xpath("./*[local-name() = '"+productType+"']"):
				value = grandChild.xpath("./*[local-name() = 'code']")
				# For when there is another <containerPackagedProduct> nested under another <asContent>
				if value[0].get('code') == None:
					subElement = grandChild.xpath(".//*[local-name() = 'asContent']")
					# subValues is an array of all <code> tags under the second instance of <asContent> 
					subValues = subElement[0].xpath(".//*[local-name() = 'code']")
					tempCodes = []
					# Loop through returned values, which come from multiple levels of <containerPackagedProducts>
					for v in subValues:
						if v.get('code') != None:
							packageProducts.append(v.get('code'))
				# Else just print the value from the first <containerPackagedProduct> level
				else:
					packageProducts.append(value[0].get('code'))
		# The getElements() function captures <manufacturedProduct> and </manufacturedProduct>, which is what
		# we're seeing when pacakageProducts has length zero
		if len(packageProducts) != 0:
			info['NDC'].append(packageProducts)

		for child in parent.iterchildren('{urn:hl7-org:v3}ingredient'):
			# Create temporary object for each ingredient
			ingredientTemp = {}
			ingredientTemp['ingredient_type'] = {}
			ingredientTemp['substance_code'] = {}

			# If statement to find active ingredients
			if child.get('classCode') == 'ACTIB' or child.get('classCode') == 'ACTIM':
				ingredientTrue = 1
				ingredientTemp['active_moiety_names'] = []

				for grandChild in child.iterchildren('{urn:hl7-org:v3}ingredientSubstance'):
					for c in grandChild.iterchildren():
						ingredientTemp['ingredient_type'] = 'active'
						if c.tag == '{urn:hl7-org:v3}name':
							active.append(c.text)
							ingredientTemp['substance_name'] = c.text
						if c.tag == '{urn:hl7-org:v3}code':
							ingredientTemp['substance_code'] = c.get('code')
						if c.tag =='{urn:hl7-org:v3}activeMoiety':
							name = c.xpath(".//*[local-name() = 'name']")
							# Send active moiety to ingredientTemp
							ingredientTemp['active_moiety_names'].append(name[0].text)

			# If statement to find inactive ingredients
			if child.get('classCode') == 'IACT':
				ingredientTrue = 1
				# Create object for each inactive ingredient
				for grandChild in child.iterchildren('{urn:hl7-org:v3}ingredientSubstance'):
					for c in grandChild.iterchildren():
						ingredientTemp['ingredient_type'] = 'inactive'

						if c.tag == '{urn:hl7-org:v3}name':
							inactive.append(c.text)
							ingredientTemp['substance_name'] = c.text

						if c.tag == '{urn:hl7-org:v3}code':
							ingredientTemp['substance_code'] = c.get('code')

			for grandChild in child.iterchildren('{urn:hl7-org:v3}quantity'):
				numerator = grandChild.xpath("./*[local-name() = 'numerator']")
				denominator = grandChild.xpath("./*[local-name() = 'denominator']")
				
				ingredientTemp['numerator_unit'] = numerator[0].get('unit')
				ingredientTemp['numerator_value'] = numerator[0].get('value')
				ingredientTemp['dominator_unit'] = denominator[0].get('unit')
				ingredientTemp['dominator_value'] = denominator[0].get('value')

			# Append temporary object to ingredients array
			if ingredientTemp['ingredient_type'] == 'inactive' and ingredientTemp['substance_code'] not in substanceCodes:
				substanceCodes.append(ingredientTemp['substance_code'])
				ingredients.append(ingredientTemp)
			if ingredientTemp['ingredient_type'] == 'active' and ingredientTemp['substance_code'] not in doses:
				substanceCodes.append(ingredientTemp['substance_code'])
				ingredients.append(ingredientTemp)
				doses.append(ingredientTemp['numerator_value'])

		# If ingredientTrue was set to 1 above, we know we have ingredient information to append
		if ingredientTrue != 0:
			info['equal_product_code'].append(equalProdCodes)
			info['SPL_INGREDIENTS'].append(active)
			info['SPL_INACTIVE_ING'].append(inactive)
		# Second set of child elements in <manufacturedProduct> used for ProdMedicines array
		def checkForValues(type, grandChild):
			value = grandChild.xpath("./*[local-name() = 'value']")
			reference = grandChild.xpath(".//*[local-name() = 'reference']")
			if type == 'SPLIMPRINT':
				value = value[0].text
			else:
				value = value[0].attrib
			kind = grandChild.find("./{urn:hl7-org:v3}code[@code='"+type+"']")
			if kind !=None:
				if type == 'SPLIMPRINT':
					info[type].append(value)
				elif type == 'SPLSCORE':
					if value.get('code') == None:
						info[type].append('')
					else:
						info[type].append(value.get('code') or value.get('value'))
				elif type == 'SPLIMAGE':
					if reference[0].get('value') == None:
						info[type].append('')
					else:
						info[type].append(reference[0].get('value'))
				else:
					info[type].append(value.get('code') or value.get('value'))


		for child in parent.iterchildren('{urn:hl7-org:v3}subjectOf'):
			 # Get approval code
			try:
				for grandChild in child.findall("{urn:hl7-org:v3}approval"):
					statusCode = grandChild.xpath("./*[local-name() = 'code']")
					info['APPROVAL_CODE'].append(statusCode[0].get('code'))
			except: 
				info['APPROVAL_CODE'].append('')
			#Get marketing act code
			for grandChild in child.findall("{urn:hl7-org:v3}marketingAct"):
				statusCode = grandChild.xpath("./*[local-name() = 'statusCode']")

				info['MARKETING_ACT_CODE'].append(statusCode[0].get('code'))
			# Get policy code
			for grandChild in child.findall("{urn:hl7-org:v3}policy"):
				for each in grandChild.iterchildren('{urn:hl7-org:v3}code'):
					info['DEA_SCHEDULE_CODE'].append(each.get('code'))
					info['DEA_SCHEDULE_NAME'].append(each.get('displayName'))
			for grandChild in child.findall("{urn:hl7-org:v3}characteristic"):
				for each in grandChild.iterchildren('{urn:hl7-org:v3}code'):
					# Run each type through the CheckForValues() function above
					type = each.get('code')
					checkForValues(type, grandChild)
					each.clear()   #clear memory
				grandChild.clear() #clear memory	
	prodMedicines.append(info)
	
	prodMedNames = ['SPLCOLOR','SPLIMAGE','SPLIMPRINT','product_name','SPLSHAPE','SPL_INGREDIENTS','SPL_INACTIVE_ING',
 	'SPLSCORE','SPLSIZE','product_code','form_code','MARKETING_ACT_CODE','DEA_SCHEDULE_CODE','DEA_SCHEDULE_NAME','NDC','equal_product_code']
	setInfoNames = ['file_name','effective_time','id_root','date_created','setid','document_type']
	sponsorNames = ['name']

	# Loop through prodMedicines as many times as there are unique product_codes, which is len(codes)

	products = []
	for i in range(0, len(codes)):
		uniqueID = setInfo['id_root'] + '-' + codes[i]
		product = {}
		product['setid_product'] = uniqueID
		product['ndc_codes'] = prodMedicines[0]['NDC'][i]
		tempProduct = {}
		for name in prodMedNames: 
			# Get information at the correct index 
			try:
				tempProduct[name] = prodMedicines[0][name][i]
			except:
				tempProduct[name] = ''
		for name in setInfoNames: 
			tempProduct[name] = setInfo[name]
		for name in sponsorNames: 
			try:
				tempProduct[name] = sponsors[name]
			except:
				tempProduct[name] = ''
		product['data'] = tempProduct 
		# Ingredients are showing duplicates again leaving out while fixing.  
		product['ingredients'] = ingredients
		products.append(product)
	return products

if __name__ == "__main__":
	test = parseData("../tmp/20130213_917046f1-4ab9-4ec3-9327-d8ec82f672f1/3abb85b1-2a3f-4106-ae5f-50af72a74723.xml")
	print test