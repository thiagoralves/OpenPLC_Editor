#!/bin/bash

# Enable strict error handling
set -o errexit      # Exit on any error
set -o pipefail     # Propagate pipeline errors
set -o nounset      # Treat unset variables as errors

# Set up error handling trap
trap 'catch_error ${LINENO}' ERR

# Error handling function
catch_error() {
    local lineno="$1"
    local error_message="Error on line $lineno: Something went wrong!"
    echo -e "\033[91m$error_message\033[0m" >&2
    exit 1
}

# Main installation logic
main() {
    # Check if installation is complete
    if ! [[ -f ".done" ]]; then
        # Execute installation with proper error handling
        if ! (bash install.sh); then
            echo -e "\033[91mInstallation failed!\033[0m" >&2
            return 1
        fi
        
        # Mark installation as complete
        if ! touch ".done"; then
            echo -e "\033[91mFailed to mark installation as complete!\033[0m" >&2
            return 1
        fi
    fi
    
    # Run editor
    if ! bash openplc_editor.sh; then
        echo -e "\033[91mFailed to start openplc_editor.sh!\033[0m" >&2
        return 1
    fi
}

# Run main function
main "$@"
