build_dmg:
	python3 setup.py bdist_dmg
build_mac:
	python3 setup.py bdist_mac
run:
	sudo python3 Blackhole.pyw

doc:

	echo -e "\033[0;32mDeploying updates to Github...\033[0m"

	# Build the project.
	cd docs && hugo

	# Add changes to git.
	git add -A

	# Commit changes.
	git commit -m "rebuilding site `date`"

	# Push source and build repos.
	git push origin master
	git subtree push --prefix=docs/public git@github.com:gliheng/blackhole.git gh-pages
