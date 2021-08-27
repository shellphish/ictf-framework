// Load dayjs, plugins and language packs.
import dayjs from 'dayjs'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'

 
// Register plugins
dayjs.extend(timezone)
dayjs.extend(utc)
 
export default dayjs