require 'yaml'
require 'redis'
require 'httparty'

# - CONFIGURATION -------------------------------------------------------------
CONFIG =  YAML.load_file('config.yml')
REDIS = Redis.new
# -----------------------------------------------------------------------------

# - MONKEY PATCHES ------------------------------------------------------------
class NilClass
  def [](*keys)
    # This makes the following not rase exceptions
    # somehash['might']['have']['this']['or']['not'].nil?
    nil
  end
end
# -----------------------------------------------------------------------------
