FROM lfoppiano/grobid:0.7.2
RUN apt-get update \
	&& apt-get install sudo \
	&& sudo apt update \
	&& sudo apt upgrade -y \ 
	&& apt-get install python3 -y \
	&& sudo apt-get install python3-pip -y \
	&& pip install xmltodict \
	&& sudo apt-get install git -y \
	&& sudo apt-get install -y python3-rdflib \
	&& git clone https://github.com/kermitt2/grobid_client_python /home/grobid_client_python \
	&& cd /home/grobid_client_python \
	&& python3 setup.py install \
	&& cd /home \
	&& mkdir /home/input
COPY fig_tab_ie.py /home/fig_tab_ie.py