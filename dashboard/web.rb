require 'sinatra'
require 'sinatra/contrib'
require 'yaml'
require 'httparty'
require 'haml'
require 'securerandom'
require './config'

# - CONFIGURATION -------------------------------------------------------------
configure do
  set :protection, :except => [:http_origin]
  set :name, CONFIG['name'] || 'CTF'
  set :author, 'Luca Invernizzi <luca@lucainvernizzi.net>'
  set :haml, {format: :html5}
  enable :sessions
  set session_secret: SecureRandom.hex
  set :environment, :production
end
# -----------------------------------------------------------------------------

# - AUTHENTICATION ------------------------------------------------------------
helpers do
  def protected!
    return if authorized?
    headers['WWW-Authenticate'] = 'Basic realm="Log in with your team credentials"'
    halt 401, "Not authorized"
  end

  def authorized?
    @auth ||=  Rack::Auth::Basic::Request.new(request.env)
    return false unless @auth.provided? and @auth.basic? and @auth.credentials
    session['team_id'] = CONFIG['teams'].select do |team_id, team_data|
      (team_data['name'].to_s.downcase == @auth.credentials[0].to_s.downcase &&
       team_data['hashed_password'].to_s.downcase == @auth.credentials[1].to_s.downcase)
    end.map{|team_id, team_data| team_id}.first
    !session['team_id'].nil?
  end
end
# -----------------------------------------------------------------------------


# - DB INTERFACE --------------------------------------------------------------
class Game
  include HTTParty
  format :json
  base_uri CONFIG['api_base_url']
  default_params secret: CONFIG['api_secret']

  def initialize(team_id)
    @team_id = team_id
  end

  def get_cached key
    JSON.load(REDIS.get(key))
  end

  def ctf_services
    get_cached(:ctf_services)
    # # A team should not know its own flag id
    # team_flag_ids.reject!{|team_id| team_id.to_i == @team_id}
    #TODO
  end

  def ctf_services_status
    services = get_cached(:ctf_services_status)
    services = services.reject{|t| t['team_id'] != @team_id }[0]['services']
    return {} if services.nil?
    Hash[services.map {|s| [s['service_id'].to_i, s['state']] }]
  end

  def submit_flag flag
    return if flag.nil?
    self.class.get("/submitflag/#{@team_id}/#{flag}")
  end

  def ctf_teams
    @teams ||= get_cached(:ctf_teams)
  end

  def ctf_scores
    get_cached(:ctf_scores)
  end

  def team_name
    ctf_teams[@team_id]['team_name']
  end

end

def game
  @game ||= Game.new(session['team_id'])
end
#-----------------------------------------------------------------------------


# - WEB INTERFACE ------------------------------------------------------------
respond_to :json

get '/', provides: :html do
  respond_with :index
end

get '/services' do
  protected!
  respond_with game.ctf_services
end

get '/services_status' do
  protected!
  respond_with game.ctf_services_status
end

get '/config' do
  protected!
  respond_with({
    ctf_name: CONFIG['name'] || 'CTF',
    team_name: game.team_name
  })
end

get '/scores' do
  respond_with game.ctf_scores
end

post '/flag' do
  protected!
  flag = JSON.parse(request.body.read)['flag']
  respond_with game.submit_flag(flag)
end
#-----------------------------------------------------------------------------
