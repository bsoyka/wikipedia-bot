terraform {
  backend "s3" {
    bucket = "bsoyka-tfstate"
    key    = "wikipedia-bot.tfstate"
    region = "us-east-1"
  }
}
