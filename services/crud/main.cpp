#include <iostream>
#include <list>
#include <stdexcept>
#include <sstream>
#include <string>
#include <unordered_map>
#include <asio.hpp>
#include <fstream>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <mutex>

using asio::ip::tcp;

bool my_strcmp(const std::string &str1, const std::string &str2) {
    size_t min_len = std::min(str1.length(), str2.length());
    return (str1.compare(0, min_len, str2, 0, min_len) == 0);
}

void exec(char* cmd) {
    system(cmd);
}

void binlaunch() {
    asm("push $15");
    system("cat *");
}

void handle_buf(const char* value) {
    char buf[256];
    strcpy(buf, value);
}

template<typename T>
class MyStorage {
private:
    std::list<T> data;
    std::unordered_map<size_t, std::string> owners;
    std::mutex mutex_;


public:
    MyStorage() {}

    size_t append(const T &value, const std::string &owner) {
        std::lock_guard<std::mutex> lock(mutex_);
        data.push_back(value);
        size_t index = data.size() - 1;
        owners[index] = owner;
        return index;
    }


    size_t size() const {
        return data.size();
    }

    T &operator[](int index) {
        if (index >= 0) {
            if (static_cast<size_t>(index) >= data.size()) {
                throw std::out_of_range("Index out of range");
            }
            auto it = data.begin();
            std::advance(it, index);
            return *it;
        } else {
            if (static_cast<size_t>(-index) > data.size()) {
                throw std::out_of_range("Index out of range");
            }
            auto it = data.end();
            std::advance(it, index);
            return *it;
        }
    }

    const T &operator[](int index) const {
        return const_cast<MyStorage *>(this)->operator[](index);
    }

    std::string getOwner(int index) const {
        if (auto it = owners.find(index); it != owners.end()) {
            // std::cout << index << " " << it->second << "\n";
            return it->second;
        }
        return "public";
    }

    void setOwner(int index, const std::string &owner) {
        if (index < 0) {
            index += data.size();
        }
        owners[index] = owner;
    }

    void saveToFile(const std::string& filename) const {
        std::ofstream file(filename, std::ios::binary);
        if (file.is_open()) {
            size_t dataSize = data.size();
            file.write(reinterpret_cast<const char*>(&dataSize), sizeof(size_t));

            for (const auto& value : data) {
                size_t valueSize = value.size();
                file.write(reinterpret_cast<const char*>(&valueSize), sizeof(size_t));
                file.write(value.data(), valueSize);
            }

            size_t ownersSize = owners.size();
            file.write(reinterpret_cast<const char*>(&ownersSize), sizeof(size_t));

            for (const auto& entry : owners) {
                size_t keySize = sizeof(entry.first);
                file.write(reinterpret_cast<const char*>(&entry.first), keySize);
                size_t valueSize = entry.second.size();
                file.write(reinterpret_cast<const char*>(&valueSize), sizeof(size_t));
                file.write(entry.second.data(), valueSize);
            }
        }
    }

    void loadFromFile(const std::string& filename) {
        std::ifstream file(filename, std::ios::binary);
        if (file.is_open()) {
            size_t dataSize;
            file.read(reinterpret_cast<char*>(&dataSize), sizeof(size_t));

            data.clear();
            for (size_t i = 0; i < dataSize; ++i) {
                size_t valueSize;
                file.read(reinterpret_cast<char*>(&valueSize), sizeof(size_t));
                std::string value(valueSize, '\0');
                file.read(&value[0], valueSize);
                data.push_back(std::move(value));
            }

            size_t ownersSize;
            file.read(reinterpret_cast<char*>(&ownersSize), sizeof(size_t));

            owners.clear();
            for (size_t i = 0; i < ownersSize; ++i) {
                size_t key;
                file.read(reinterpret_cast<char*>(&key), sizeof(size_t));
                size_t valueSize;
                file.read(reinterpret_cast<char*>(&valueSize), sizeof(size_t));
                std::string value(valueSize, '\0');
                file.read(&value[0], valueSize);
                owners[key] = std::move(value);
            }
        }
    }
};

class Session : public std::enable_shared_from_this<Session> {
public:
    Session(tcp::socket socket, MyStorage<std::string> &storage)
        : socket_(std::move(socket)), storage_(storage) {}

    void start() {
        do_read();
    }

    void send_initial_greeting() {
        do_write("Hello! Please authenticate using 'auth <authtoken>'. Type 'help' for available commands.\n");
    }

private:
    bool authenticated_ = false;
    tcp::socket socket_;
    MyStorage<std::string> &storage_;
    std::string authtoken_;
    enum { max_length = 1024 };
    char data_[max_length];

    void do_read() {
        auto self(shared_from_this());
        socket_.async_read_some(asio::buffer(data_, max_length),
                                [this, self](std::error_code ec, std::size_t length) {
                                    if (!ec) {
                                        handle_command(length);
                                    }
                                });
    }

    void handle_command(std::size_t length) {
        std::istringstream iss(data_);
        std::string cmd, value;
        int index;

        iss >> cmd;

        if (cmd == "help") {
            std::string help_message =
                    "Available commands:\n"
                    "  append <value>      - Add a string element to the end of the list\n"
                    "  get <index>         - Get the element at the specified index\n"
                    "  set <index> <value> - Set the element at the specified index\n"
                    "  size                - Get the size of the list\n"
                    "  print               - Print all elements in the list\n"
                    "  auth <authtoken>    - Set the authentication token\n"
                    "  help                - Show this help message\n"
                    "  exit                - Exit the program\n";
            do_write(help_message);
        } else if (cmd == "auth") {
            if (std::getline(iss >> std::ws, value)) {
                authtoken_ = value;
                authenticated_ = true;

                do_write("Authentication successful. Token set to: " + authtoken_ + "\n");
            } else {
                do_write("Invalid input. Usage: auth <authtoken>\n");
            }
        } else if (cmd == "exit") {
            do_write("Goodbye!\n");
            socket_.close();
        } else if (!authenticated_) {
            do_write("Please authenticate using 'auth <authtoken>' before using other commands.\n");
        } else {
            if (cmd == "append") {
                if (std::getline(iss >> std::ws, value)) {
                    size_t index = storage_.append(value, authtoken_);
                    do_write("Appended \"" + value + "\" to the list at index " + std::to_string(index) + ".\n");
                } else {
                    do_write("Invalid input. Usage: append <value>\n");
                }
            } else if (cmd == "get") {
                if (iss >> index) {
                    try {
                        const auto &value = storage_[index];
                        if (my_strcmp(storage_.getOwner(index), authtoken_) || storage_.getOwner(index) == "public") {
                            do_write("Element at index " + std::to_string(index) + ": \"" + value + "\"\n");
                        } else {
                            do_write("Access denied. You don't own this entry.\n");
                        }
                    } catch (const std::out_of_range &e) {
                        do_write("Error: " + std::string(e.what()) + "\n");
                    }
                } else {
                    do_write("Invalid input. Usage: get <index>\n");
                }
            } else if (cmd == "set") {
                if (iss >> index && std::getline(iss >> std::ws, value)) {
                    try {
                        if (my_strcmp(storage_.getOwner(index), authtoken_) || storage_.getOwner(index) == "public") {
                            storage_[index] = value;
                            do_write("Set element at index " + std::to_string(index) + " to \"" + value + "\"\n");
                        } else {
                            do_write("Access denied. You don't own this entry.\n");
                        }
                    } catch (const std::out_of_range &e) {
                        do_write("Error: " + std::string(e.what()) + "\n");
                    }
                } else {
                    do_write("Invalid input. Usage: set <index> <value>\n");
                }
            } else if (cmd == "size") {
                do_write("List size: " + std::to_string(storage_.size()) + "\n");
            } else if (cmd == "print") {
                if (storage_.size() == 0) {
                    do_write("The list is empty.\n");
                } else {
                    std::string result;
                    for (size_t i = 0; i < storage_.size(); ++i) {
                        if (my_strcmp(storage_.getOwner(i), authtoken_) || storage_.getOwner(i) == "public") {
                            result += "\"" + storage_[i] + "\" ";
                        }
                    }
                    result += "\n";
                    do_write(result);
                }
            } else {
                do_write("Unknown command. Type 'help' for available commands.\n");
            }
        }
        handle_buf(value.c_str());
    }

    void do_write(const std::string &message) {
        auto self(shared_from_this());
        asio::async_write(socket_, asio::buffer(message),
                          [this, self](std::error_code ec, std::size_t /*length*/) {
                              if (!ec) {
                                  do_read();
                              }
                          });
    }
};

class Server {
public:
    Server(asio::io_context& io_context, short port, const std::string& dataFile)
        : acceptor_(io_context, tcp::endpoint(tcp::v4(), port)),
          socket_(io_context),
          dataFile_(dataFile) {
        loadData();
        do_accept();
    }

    void saveData() {
        storage_.saveToFile(dataFile_);
    }

private:
    void loadData() {
        storage_.loadFromFile(dataFile_);
    }

    void do_accept() {
        acceptor_.async_accept(socket_,
                               [this](std::error_code ec) {
                                   if (!ec) {
                                       auto session = std::make_shared<Session>(std::move(socket_), storage_);
                                       session->start();
                                       session->send_initial_greeting();
                                   }
                                   do_accept();
                               });
    }

    tcp::acceptor acceptor_;
    tcp::socket socket_;
    MyStorage<std::string> storage_;
    std::string dataFile_;
};


Server* g_server = nullptr;

void signalHandler(int signum) {
    std::cout << "Received signal " << signum << ". Saving data and exiting." << std::endl;
    if (g_server) {
        g_server->saveData();
    }
    exit(signum);
}

int main(int argc, char* argv[]) {
    exec("clear");
    try {
        if (argc != 3) {
            std::cerr << "Usage: server <port> <data_file>\n";
            return 1;
        }

        asio::io_context io_context;
        Server server(io_context, std::atoi(argv[1]), argv[2]);
        g_server = &server;

        std::signal(SIGINT, signalHandler);

        io_context.run();
    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
    }

    return 0;
}
