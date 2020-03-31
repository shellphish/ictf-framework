import mixin from 'universal-mixin';
import _ from 'underscore';

export default mixin({
  filterAcademicTeams(teams, academiconly) {
    if (teams === undefined) {
      return [];
    }
    return _.values(teams).filter(team => {
      if (academiconly == 'true') {
        return team.academic_team == 1;
      }
      else {
        return true;
      }
    });
  }
});
