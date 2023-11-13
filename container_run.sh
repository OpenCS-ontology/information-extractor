batch_size=5
archives=("scpe" "csis")

jq '.timeout = 120' /home/grobid_client_python/config.json >tmpfile
mv tmpfile /home/grobid_client_python/config.json

for archive in "${archives[@]}"; do
    input_ttls_for_archive=/home/input_ttl_files/$archive
    output_ttls_for_archive=/home/output_ttl_files/$archive

    if [ ! -d "$input_ttls_for_archive" ]; then
        mkdir $input_ttls_for_archive
    fi

    if [ ! -d "$output_ttls_for_archive" ]; then
        mkdir $output_ttls_for_archive
    fi

    for dir in "/input_pdf_files/$archive"/*; do
        if [ -d "$dir" ]; then
            rm -rf /home/input/
            rm -rf /home/output_xml_files/

            mkdir /home/input/
            mkdir /home/output_xml_files/

            volume_for_out_ttls=/home/output_ttl_files/$archive/$(basename "$dir")
            if [ ! -d "$volume_for_out_ttls" ]; then
                mkdir $volume_for_out_ttls
            fi

            num_in_batch=1

            for file in "$dir"/*; do
                if [ -f "$file" ]; then
                    cp "$file" /home/input/$(basename "$file" .pdf).pdf
                    if [ "$((num_in_batch % $((batch_size))))" -ne 0 ]; then
                        num_in_batch=$((num_in_batch + 1))
                    else
                        python3 /home/fig_tab_ie.py /home/input /home/output_ttl_files/$archive/$(basename "$dir")

                        num_in_batch=1

                        rm -rf /home/input/
                        rm -rf /home/output_xml_files/

                        mkdir /home/input/
                        mkdir /home/output_xml_files/
                    fi

                fi
            done
            if [ "$((num_in_batch % $((batch_size + 1))))" -ne 0 ]; then
                python3 /home/fig_tab_ie.py /home/input /home/output_ttl_files/$archive/$(basename "$dir")
            fi
        fi
    done
done

python3 /home/merge_ttl_files.py
cp -r /home/input_ttl_files/* /home/final_ttls_for_every_run
