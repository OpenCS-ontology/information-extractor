docker pull lfoppiano/grobid:0.7.2
docker build --no-cache -t fig_tab_ie .

:: docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.7.2