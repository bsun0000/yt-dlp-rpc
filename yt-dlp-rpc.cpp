#include <iostream>
#include <curl/curl.h>

size_t writeFunction(void* ptr, size_t size, size_t nmemb, std::string* data) {
	data->append((char*)ptr, size * nmemb);
	return size * nmemb;
}

int main(int argc, char** argv) {
	curl_global_init(CURL_GLOBAL_DEFAULT);
	auto curl = curl_easy_init();
	if (!curl)
		return 1;

	std::string fields;
	for (int i = 1; i < argc; i++) {
		fields.append(argv[i]);
		if (i < (argc - 1)) {
			fields.append("\n");
		}
	}

	curl_easy_setopt(curl, CURLOPT_POST, true);
	curl_easy_setopt(curl, CURLOPT_POSTFIELDS, fields.c_str());
	curl_easy_setopt(curl, CURLOPT_URL, "http://127.0.0.1:9120/");
	curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 1L);
	curl_easy_setopt(curl, CURLOPT_MAXREDIRS, 50L);
	curl_easy_setopt(curl, CURLOPT_TCP_KEEPALIVE, 0L);
	curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, false);
	curl_easy_setopt(curl, CURLOPT_TCP_FASTOPEN, true);

	std::string response_string;
	std::string header_string;
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeFunction);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);
	curl_easy_setopt(curl, CURLOPT_HEADERDATA, &header_string);

	curl_easy_perform(curl);

	curl_easy_cleanup(curl);
	curl_global_cleanup();
	curl = NULL;

	std::cout << response_string;

	return (0);
}
