python scripts/copy_docs.py doc .tmp/doc
sphinx-build -W -E -b html .tmp/doc .tmp/html
python scripts/copy_docs.py .tmp/html built_docs
echo $null >> built_docs/.nojekyll
