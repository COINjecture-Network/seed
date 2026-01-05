# Makefile for OQS Kyber Test
# Builds the Kyber key exchange test against liboqs

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99
TARGET = kyber_test
SRC = kyber_test.c

# Default to local liboqs installation
LIBOQS_INSTALL_DIR ?= $(CURDIR)/liboqs-install

# Include and library paths
INCLUDES = -I$(LIBOQS_INSTALL_DIR)/include
LDFLAGS = -L$(LIBOQS_INSTALL_DIR)/lib
LIBS = -loqs

# Check if we should use system liboqs instead
ifdef USE_SYSTEM_LIBOQS
    INCLUDES =
    LDFLAGS =
endif

.PHONY: all clean test help

all: $(TARGET)

$(TARGET): $(SRC)
	@echo "Building $(TARGET)..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $(TARGET) $(SRC) $(LDFLAGS) $(LIBS)
	@echo "Build successful!"

test: $(TARGET)
	@echo "Running Kyber-768 key exchange test..."
	@if [ -d "$(LIBOQS_INSTALL_DIR)/lib" ] && [ -z "$(USE_SYSTEM_LIBOQS)" ]; then \
		export LD_LIBRARY_PATH="$(LIBOQS_INSTALL_DIR)/lib:$$LD_LIBRARY_PATH"; \
		./$(TARGET); \
	else \
		./$(TARGET); \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -f $(TARGET)
	@echo "Clean complete!"

help:
	@echo "OQS Kyber Test Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all   - Build the Kyber test (default)"
	@echo "  test  - Build and run the Kyber test"
	@echo "  clean - Remove build artifacts"
	@echo "  help  - Show this help message"
	@echo ""
	@echo "Options:"
	@echo "  LIBOQS_INSTALL_DIR - Path to liboqs installation (default: ./liboqs-install)"
	@echo "  USE_SYSTEM_LIBOQS  - Use system-installed liboqs instead of local"
	@echo ""
	@echo "Examples:"
	@echo "  make                                    # Build with local liboqs"
	@echo "  make test                               # Build and run test"
	@echo "  make USE_SYSTEM_LIBOQS=1               # Build with system liboqs"
	@echo "  make LIBOQS_INSTALL_DIR=/usr/local     # Build with custom path"
