# Workflow Readme

1. deploy.yml:
   - On pushes to main, renders quarto website in main and then commits the rendered site to `gh-pages` branch.
2. build_preview.yml:
   - Renders the pull request to `gh-pages/previews/[pull-request number]`
     - Link to the preview in the pull request comments (may take a few minutes - refresh if you get 404 page)
       - Can also find the preview at `https://surge-neurotech-club.github.io/preview/pr-[pull-request-#]/`

**Note:** both workflows create a python environment from `requirements.txt` if running into errors, check the versions or if the required package(s) is in the requirements.txt