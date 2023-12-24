FROM rocm/tensorflow:rocm5.7-tf2.13-dev


RUN pip install stardist gputools edt 
RUN pip install "arkitekt[all]==0.5.57"
RUN pip install "pydantic<2"

RUN mkdir /workspace
COPY . /workspace
WORKDIR /workspace
