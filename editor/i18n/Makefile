all:
	@echo "Please specify target 'source_list', 'template' or 'locales'"

template:
	@echo To generate translation template message.pot file:
	python mki18n.py -p --domain=Beremiz

locales:
	@echo "Generate .mo files for all languages:"
	python mki18n.py -m --moTarget=../locale --domain=Beremiz


source_list:
	echo @To "Generate list with source files: app.fil:"
	find .. -name "*.py" -exec grep -q '_(' {} ';' -print -o -name "*XSD*" -print -o -name "*.csv" -print | grep -v '/build/' | grep -v '/pyjs/' > app.fil
	echo "../plcopen/Additional_Function_Blocks.xml" >> app.fil
	echo "../plcopen/Standard_Function_Blocks.xml"   >> app.fil

transifex_init:
	tx init --skipsetup

transifex_pull:
	tx pull --all
	find . -name '*.po' -exec sed -i 's/charset=CHARSET/charset=UTF-8/' {} \;


.PHONY: all, template, locales, source_list
