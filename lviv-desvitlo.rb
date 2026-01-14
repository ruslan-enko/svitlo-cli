# Lviv DeSvitlo Formula for Homebrew
class LvivDesvitlo < Formula
  desc "Terminal TUI app for monitoring power outage schedules in Lviv"
  homepage "https://github.com/your-username/Lviv-DeSvitlo"
  url "https://github.com/your-username/Lviv-DeSvitlo/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "your_sha256_hash_here"
  license "MIT"

  depends_on "python@3.9"

  def install
    # Install Python dependencies
    system "pip3", "install", "-r", "requirements.txt"
    
    # Install the package
    system "pip3", "install", "-e", "."
    
    # Create symlink in bin
    bin.install_symlink libexec/"bin/lviv-desvitlo"
  end

  test do
    system "#{bin}/lviv-desvitlo", "--help"
  end
end